import shutil
import textwrap
from typing import List

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel

from term_agent.schemas import ManualSuggestion


class ConsoleUI:
    REGENERATE_CHOICE = "__regenerate_suggestion__"

    def __init__(self) -> None:
        self.console = Console()

    def get_prompt(self) -> str:
        return input("Enter your request: ").strip()

    def show_reply(self, reply: str) -> None:
        if reply.strip():
            self.console.print(Panel(reply.strip(), title="Assistant Reply", border_style="cyan"))

    def show_suggestions(self, suggestions: List[ManualSuggestion]) -> None:
        if not suggestions:
            self.console.print("[yellow]No executable command suggestions.[/yellow]")

    def choose_command(self, suggestions: List[ManualSuggestion]) -> str | None:
        terminal_width = shutil.get_terminal_size((120, 20)).columns
        max_width = max(40, terminal_width - 8)
        choices: List[Choice] = []
        for suggestion in suggestions:
            command_line = textwrap.fill(
                suggestion.command,
                width=max_width,
                subsequent_indent="   ",
            )
            description_line = textwrap.fill(
                suggestion.description,
                width=max_width,
                subsequent_indent="   ",
            )
            title = f"{command_line}\n   {description_line}"
            choices.append(Choice(name=title, value=suggestion.command))
        choices.append(Choice(name="Generate a new suggestion", value=self.REGENERATE_CHOICE))
        choices.append(Choice(name="Dismiss", value=""))
        selection = inquirer.select(
            message="Use ↑/↓ to choose a command and Enter to execute:",
            choices=choices,
            default=choices[0].value,
            cycle=False,
        ).execute()
        if not selection:
            return None
        return str(selection)
