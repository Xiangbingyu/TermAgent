import json
import os
import platform
import tempfile
from collections import deque
from typing import List

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from term_agent.llm import build_chat_model
from term_agent.prompts import manual_prompt
from term_agent.schemas import ManualResult, ManualSuggestion
from term_agent.config import AppConfig


class GenerateInstructionsArgs(BaseModel):
    commands: List[str] = Field(
        description="候选可执行命令列表，每个命令应可直接在终端执行。"
    )
    descriptions: List[str] = Field(
        description="与 commands 一一对应的中文说明列表。"
    )


class ManualMode:
    def __init__(self, config: AppConfig) -> None:
        tool = StructuredTool.from_function(
            func=self.generate_instructions,
            name="generate_instructions",
            description="生成最终指令与描述。参数: commands, descriptions。",
            args_schema=GenerateInstructionsArgs,
        )
        self.chat = build_chat_model(config)
        self.chat_with_tools = self.chat.bind_tools([tool])
        self.prompt = manual_prompt()
        self.history: deque[BaseMessage] = deque(maxlen=80)
        self.executed_commands: deque[str] = deque(
            self._load_session_commands(),
            maxlen=200,
        )

    def suggest(self, user_input: str, current_directory: str) -> ManualResult:
        prompt_messages = self.prompt.format_messages(user_input=user_input)
        system_message = prompt_messages[0]
        current_message = HumanMessage(content=user_input)
        runtime_message = self._build_runtime_message(current_directory)
        command_history_message = self._build_command_history_message()
        context_messages = [runtime_message, *self.history]
        if command_history_message:
            context_messages.append(command_history_message)
        messages = [system_message, *context_messages, current_message]
        response = self.chat_with_tools.invoke(messages)
        self.history.append(current_message)
        self.history.append(response)
        tool_calls = getattr(response, "tool_calls", []) or []
        for call in tool_calls:
            if str(call.get("name", "")) != "generate_instructions":
                continue
            args = call.get("args", {}) or {}
            commands_raw = args.get("commands", []) or []
            descriptions_raw = args.get("descriptions", []) or []
            commands = commands_raw if isinstance(commands_raw, list) else [commands_raw]
            descriptions = descriptions_raw if isinstance(descriptions_raw, list) else [descriptions_raw]
            suggestions = [
                ManualSuggestion(command=str(command), description=str(description))
                for command, description in zip(commands, descriptions)
            ]
            return ManualResult(suggestions=suggestions)
        return ManualResult(suggestions=[])

    def record_regenerate_request(self, suggestions: List[ManualSuggestion]) -> None:
        if suggestions:
            suggestion_lines = "\n".join(
                f"- {item.command} | {item.description}" for item in suggestions
            )
            content = (
                "用户选择了 Generate a new suggestion，请基于以下已有候选继续优化：\n"
                f"{suggestion_lines}"
            )
        else:
            content = "用户选择了 Generate a new suggestion，请继续生成新候选。"
        self.history.append(HumanMessage(content=content))

    def record_dismiss_request(self, suggestions: List[ManualSuggestion]) -> None:
        if suggestions:
            suggestion_lines = "\n".join(
                f"- {item.command} | {item.description}" for item in suggestions
            )
            content = (
                "用户选择了 Dismiss，本轮未执行命令。候选如下：\n"
                f"{suggestion_lines}"
            )
        else:
            content = "用户选择了 Dismiss，本轮未执行命令。"
        self.executed_commands.append(content)
        self._save_session_commands()
        self.history.append(HumanMessage(content=content))

    def record_executed_command(self, command: str) -> None:
        normalized = command.strip()
        if not normalized:
            return
        self.executed_commands.append(normalized)
        self._save_session_commands()
        self.history.append(HumanMessage(content=f"终端已执行命令: {normalized}"))

    def record_command_result(
        self,
        command: str,
        return_code: int,
        stdout: str,
        stderr: str,
        cwd: str,
    ) -> None:
        normalized = command.strip()
        if not normalized:
            return
        stdout_text = self._limit_text(stdout.strip())
        stderr_text = self._limit_text(stderr.strip())
        output_text = stdout_text or "无"
        error_text = stderr_text or "无"
        summary = (
            "命令执行结果:\n"
            f"- 命令: {normalized}\n"
            f"- 工作目录: {cwd}\n"
            f"- 退出码: {return_code}\n"
            f"- 标准输出: {output_text}\n"
            f"- 错误输出: {error_text}"
        )
        self.executed_commands.append(summary)
        self._save_session_commands()
        self.history.append(HumanMessage(content=summary))

    def _build_command_history_message(self) -> HumanMessage | None:
        if not self.executed_commands:
            return None
        commands = "\n".join(
            f"{index + 1}. {command}"
            for index, command in enumerate(self.executed_commands)
        )
        return HumanMessage(
            content=(
                "当前终端已执行命令记录（终端关闭后清空）：\n"
                f"{commands}"
            )
        )

    def _build_runtime_message(self, current_directory: str) -> HumanMessage:
        resolved_directory = current_directory.strip() or os.getcwd()
        return HumanMessage(
            content=(
                "当前运行环境:\n"
                f"- 操作系统: {platform.system()} ({os.name})\n"
                f"- 当前目录: {resolved_directory}"
            )
        )

    def _limit_text(self, content: str, max_chars: int = 1200) -> str:
        if len(content) <= max_chars:
            return content
        return f"{content[:max_chars]}...(已截断)"

    def _session_file_path(self) -> str:
        parent_pid = os.getppid()
        base_dir = os.path.join(tempfile.gettempdir(), "term-agent-manual")
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, f"{parent_pid}.json")

    def _load_session_commands(self) -> List[str]:
        path = self._session_file_path()
        try:
            with open(path, "r", encoding="utf-8") as file:
                payload = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        commands = payload.get("commands", [])
        if not isinstance(commands, list):
            return []
        return [str(item) for item in commands]

    def _save_session_commands(self) -> None:
        path = self._session_file_path()
        payload = {"commands": list(self.executed_commands)}
        with open(path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False)

    def generate_instructions(
        self,
        commands: List[str],
        descriptions: List[str],
    ) -> str:
        payload = {
            "commands": commands,
            "descriptions": descriptions,
        }
        return json.dumps(payload, ensure_ascii=False)
