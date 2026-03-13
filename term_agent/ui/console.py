from typing import List

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console

from term_agent.schemas import ManualSuggestion


class ConsoleUI:
    REGENERATE_CHOICE = "__regenerate_suggestion__"

    def __init__(self) -> None:
        self.console = Console()

    def get_prompt(
        self, current_directory: str | None = None, python_prefix: str | None = None
    ) -> str:
        if current_directory:
            env_label = f" [python:{python_prefix}]" if python_prefix else ""
            return input(
                f"\n({current_directory}){env_label} \u2192 Enter your request: "
            ).strip()
        return input("Enter your request: ").strip()

    def show_suggestions(self, suggestions: List[ManualSuggestion]) -> None:
        if not suggestions:
            self.console.print("[yellow]No executable command suggestions.[/yellow]")

    def choose_command(self, suggestions: List[ManualSuggestion]) -> str | None:
        choices: List[Choice] = []
        for suggestion in suggestions:
            title = f"{suggestion.command}\n# {suggestion.description}"
            choices.append(Choice(name=title, value=suggestion.command))
        choices.append(Choice(name="Generate a new suggestion", value=self.REGENERATE_CHOICE))
        choices.append(Choice(name="Dismiss", value=""))
        selection = inquirer.select(
            message="Select a command:",
            choices=choices,
            default=choices[0].value,
            cycle=False,
        ).execute()
        if not selection:
            return None
        return str(selection)
