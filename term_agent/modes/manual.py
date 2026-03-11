import json
from typing import List

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from term_agent.llm import build_chat_model
from term_agent.prompts import manual_prompt
from term_agent.schemas import ManualResult, ManualSuggestion
from term_agent.config import AppConfig


class GenerateInstructionsArgs(BaseModel):
    reply: str = Field(description="给用户展示的最终回复文本。")
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
            description="生成最终指令与描述。参数: reply, commands, descriptions。",
            args_schema=GenerateInstructionsArgs,
        )
        self.chat = build_chat_model(config)
        self.chat_with_tools = self.chat.bind_tools([tool])
        self.prompt = manual_prompt()

    def suggest(self, user_input: str) -> ManualResult:
        messages = self.prompt.format_messages(user_input=user_input)
        response = self.chat_with_tools.invoke(messages)
        tool_calls = getattr(response, "tool_calls", []) or []
        for call in tool_calls:
            if str(call.get("name", "")) != "generate_instructions":
                continue
            args = call.get("args", {}) or {}
            reply = str(args.get("reply", ""))
            commands_raw = args.get("commands", []) or []
            descriptions_raw = args.get("descriptions", []) or []
            commands = commands_raw if isinstance(commands_raw, list) else [commands_raw]
            descriptions = descriptions_raw if isinstance(descriptions_raw, list) else [descriptions_raw]
            suggestions = [
                ManualSuggestion(command=str(command), description=str(description))
                for command, description in zip(commands, descriptions)
            ]
            return ManualResult(reply=reply, suggestions=suggestions)
        return ManualResult(reply=str(response.content).strip() or "未能生成可执行指令。", suggestions=[])

    def generate_instructions(
        self,
        reply: str,
        commands: List[str],
        descriptions: List[str],
    ) -> str:
        payload = {
            "reply": reply,
            "commands": commands,
            "descriptions": descriptions,
        }
        return json.dumps(payload, ensure_ascii=False)
