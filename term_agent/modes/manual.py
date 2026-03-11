import json
from typing import List

from term_agent.llm import build_chat_model
from term_agent.prompts import manual_prompt
from term_agent.schemas import ManualResult, ManualSuggestion
from term_agent.config import AppConfig


class ManualMode:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.chat = build_chat_model(config)
        self.prompt = manual_prompt()

    def suggest(self, user_input: str) -> ManualResult:
        messages = self.prompt.format_messages(user_input=user_input)
        response = self.chat.invoke(messages)
        commands = self._parse_commands(response.content)
        suggestions = [ManualSuggestion(command=cmd) for cmd in commands]
        return ManualResult(suggestions=suggestions)

    def _parse_commands(self, content: str) -> List[str]:
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return [str(item).strip() for item in data if str(item).strip()]
        except json.JSONDecodeError:
            pass
        return [content.strip()] if content.strip() else []
