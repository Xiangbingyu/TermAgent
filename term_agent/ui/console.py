from typing import List


class ConsoleUI:
    def get_prompt(self) -> str:
        return input("Enter your request: ").strip()

    def show_suggestions(self, commands: List[str]) -> None:
        for index, command in enumerate(commands, start=1):
            print(f"[{index}] {command}")

    def choose_command(self, commands: List[str]) -> str | None:
        if not commands:
            return None
        selection = input("Enter a number to execute, or press Enter to cancel: ").strip()
        if not selection:
            return None
        try:
            position = int(selection) - 1
        except ValueError:
            return None
        if 0 <= position < len(commands):
            return commands[position]
        return None
