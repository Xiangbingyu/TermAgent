from term_agent.modes import AutoMode
from term_agent.executor import CommandExecutor
from term_agent.config import AppConfig


class AgentEngine:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.auto_mode = AutoMode(config)
        self.executor = CommandExecutor()

    def run(self, user_input: str) -> None:
        action = self.auto_mode.next_action(user_input)
        command = action.get("command")
        if command:
            self.executor.run(command)
