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
        description="Candidate executable commands. Each command must run directly in terminal."
    )
    descriptions: List[str] = Field(
        description="Descriptions aligned one-to-one with commands."
    )


class ManualMode:
    def __init__(self, config: AppConfig) -> None:
        tool = StructuredTool.from_function(
            func=self.generate_instructions,
            name="generate_instructions",
            description="Generate final commands and descriptions. Args: commands, descriptions.",
            args_schema=GenerateInstructionsArgs,
        )
        self.chat = build_chat_model(config)
        self.chat_with_tools = self.chat.bind_tools([tool])
        self.prompt = manual_prompt()
        self.history: deque[BaseMessage] = deque(maxlen=80)
        session_state = self._load_session_state()
        self.executed_commands: deque[str] = deque(
            session_state["commands"],
            maxlen=200,
        )
        self.user_queries: deque[str] = deque(
            session_state["user_queries"],
            maxlen=200,
        )
        self.result_records: deque[str] = deque(
            session_state["results"],
            maxlen=200,
        )

    def suggest(self, user_input: str, current_directory: str) -> ManualResult:
        prompt_messages = self.prompt.format_messages(
            user_input=user_input,
            basic_information_section=self._build_basic_information_section(
                current_directory
            ),
            history_section=self._build_history_section(),
        )
        system_message = prompt_messages[0]
        current_message = prompt_messages[1]
        messages = [system_message, *self.history, current_message]
        response = self.chat_with_tools.invoke(messages)
        normalized_query = user_input.strip()
        if normalized_query:
            self.user_queries.append(normalized_query)
            self._persist_session_state()
        self.history.append(current_message)
        self.history.append(response)
        suggestions = self._extract_suggestions_from_tool_calls(
            getattr(response, "tool_calls", []) or []
        )
        if suggestions:
            return ManualResult(suggestions=suggestions)
        return ManualResult(suggestions=[])

    def record_regenerate_request(self, suggestions: List[ManualSuggestion]) -> None:
        if suggestions:
            suggestion_lines = "\n".join(
                f"- {item.command} | {item.description}" for item in suggestions
            )
            content = (
                "User selected Generate a new suggestion. Refine from these candidates:\n"
                f"{suggestion_lines}"
            )
        else:
            content = (
                "User selected Generate a new suggestion. Continue generating new candidates."
            )
        self.result_records.append(content)
        self._persist_session_state()
        self.history.append(HumanMessage(content=content))

    def record_dismiss_request(self, suggestions: List[ManualSuggestion]) -> None:
        if suggestions:
            suggestion_lines = "\n".join(
                f"- {item.command} | {item.description}" for item in suggestions
            )
            content = (
                "User selected Dismiss. No command was executed in this round. Candidates:\n"
                f"{suggestion_lines}"
            )
        else:
            content = "User selected Dismiss. No command was executed in this round."
        self.result_records.append(content)
        self._persist_session_state()
        self.history.append(HumanMessage(content=content))

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
        self.executed_commands.append(normalized)
        stdout_text = stdout.strip()
        if len(stdout_text) > 1200:
            stdout_text = f"{stdout_text[:1200]}...(truncated)"
        stderr_text = stderr.strip()
        if len(stderr_text) > 1200:
            stderr_text = f"{stderr_text[:1200]}...(truncated)"
        output_text = stdout_text or "None"
        error_text = stderr_text or "None"
        summary = (
            "Command execution result:\n"
            f"- Command: {normalized}\n"
            f"- Working directory: {cwd}\n"
            f"- Exit code: {return_code}\n"
            f"- Stdout: {output_text}\n"
            f"- Stderr: {error_text}"
        )
        self.result_records.append(summary)
        self._persist_session_state()
        self.history.append(HumanMessage(content=summary))

    def record_user_query(self, query: str) -> None:
        normalized = query.strip()
        if not normalized:
            return
        self.user_queries.append(normalized)
        self._persist_session_state()

    def _build_basic_information_section(self, current_directory: str) -> str:
        resolved_directory = current_directory.strip() or os.getcwd()
        return "\n".join(
            [
                f"- Operating system: {platform.system()} ({os.name})",
                f"- Working directory: {resolved_directory}",
            ]
        )

    def _build_history_section(self) -> str:
        queries = list(self.user_queries)
        commands = list(self.executed_commands)
        results = list(self.result_records)
        if not queries and not commands and not results:
            return "0. No history available."
        lines: List[str] = []
        max_len = max(len(queries), len(commands), len(results))
        for index in range(max_len):
            query = queries[index] if index < len(queries) else "None"
            command = commands[index] if index < len(commands) else "None"
            result = results[index] if index < len(results) else "None"
            lines.append(f"{index + 1}. Request: {query}")
            lines.append(f"   - Command: {command}")
            result_lines = str(result).splitlines() or [""]
            lines.append(f"   - Result: {result_lines[0]}")
            for line in result_lines[1:]:
                lines.append(f"     {line}")
        return "\n".join(lines)

    def _extract_suggestions_from_tool_calls(self, tool_calls: List[dict]) -> List[ManualSuggestion]:
        for call in tool_calls:
            if str(call.get("name", "")) != "generate_instructions":
                continue
            args = call.get("args", {}) or {}
            commands = self._normalize_string_list(args.get("commands", []))
            descriptions = self._normalize_string_list(args.get("descriptions", []))
            if not commands:
                return []
            if len(descriptions) < len(commands):
                descriptions.extend([""] * (len(commands) - len(descriptions)))
            return [
                ManualSuggestion(command=command, description=descriptions[index])
                for index, command in enumerate(commands)
            ]
        return []

    def _normalize_string_list(self, raw: object) -> List[str]:
        if isinstance(raw, list):
            return [str(item) for item in raw]
        if raw is None:
            return []
        return [str(raw)]

    def _load_session_state(self) -> dict[str, List[str]]:
        parent_pid = os.getppid()
        base_dir = os.path.join(tempfile.gettempdir(), "term-agent-manual")
        os.makedirs(base_dir, exist_ok=True)
        path = os.path.join(base_dir, f"{parent_pid}.json")
        try:
            with open(path, "r", encoding="utf-8") as file:
                payload = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"commands": [], "user_queries": [], "results": []}
        if not isinstance(payload, dict):
            return {"commands": [], "user_queries": [], "results": []}
        commands_raw = payload.get("commands", [])
        if isinstance(commands_raw, list):
            commands = [str(item) for item in commands_raw]
        else:
            commands = []
        user_queries_raw = payload.get("user_queries", [])
        if isinstance(user_queries_raw, list):
            user_queries = [str(item) for item in user_queries_raw]
        else:
            user_queries = []
        results_raw = payload.get("results", [])
        if isinstance(results_raw, list):
            results = [str(item) for item in results_raw]
        else:
            results = []
        return {
            "commands": commands,
            "user_queries": user_queries,
            "results": results,
        }

    def _persist_session_state(self) -> None:
        payload = {
            "commands": list(self.executed_commands),
            "user_queries": list(self.user_queries),
            "results": list(self.result_records),
        }
        parent_pid = os.getppid()
        base_dir = os.path.join(tempfile.gettempdir(), "term-agent-manual")
        os.makedirs(base_dir, exist_ok=True)
        path = os.path.join(base_dir, f"{parent_pid}.json")
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
