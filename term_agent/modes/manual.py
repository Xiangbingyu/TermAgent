import json
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
        self.history: deque[BaseMessage] = deque(maxlen=20)

    def suggest(self, user_input: str) -> ManualResult:
        prompt_messages = self.prompt.format_messages(user_input=user_input)
        system_message = prompt_messages[0]
        current_message = HumanMessage(content=user_input)
        messages = [system_message, *self.history, current_message]
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
