import json
from collections import deque
from typing import Dict, Any

from langchain_core.messages import BaseMessage, HumanMessage
from term_agent.llm import build_chat_model
from term_agent.prompts import auto_prompt
from term_agent.config import AppConfig


class AutoMode:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.chat = build_chat_model(config)
        self.prompt = auto_prompt()
        self.history: deque[BaseMessage] = deque(maxlen=20)

    def next_action(self, user_input: str) -> Dict[str, Any]:
        prompt_messages = self.prompt.format_messages(user_input=user_input)
        system_message = prompt_messages[0]
        current_message = HumanMessage(content=user_input)
        messages = [system_message, *self.history, current_message]
        response = self.chat.invoke(messages)
        self.history.append(current_message)
        self.history.append(response)
        return self._parse_action(response.content)

    def _parse_action(self, content: str) -> Dict[str, Any]:
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        return {"action": "respond", "command": content.strip()}
