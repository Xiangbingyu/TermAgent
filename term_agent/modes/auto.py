import json
from typing import Dict, Any

from term_agent.llm import build_chat_model
from term_agent.prompts import auto_prompt
from term_agent.config import AppConfig


class AutoMode:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.chat = build_chat_model(config)
        self.prompt = auto_prompt()

    def next_action(self, user_input: str) -> Dict[str, Any]:
        messages = self.prompt.format_messages(user_input=user_input)
        response = self.chat.invoke(messages)
        return self._parse_action(response.content)

    def _parse_action(self, content: str) -> Dict[str, Any]:
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        return {"action": "respond", "command": content.strip()}
