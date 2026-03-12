import argparse
import os
import sys

from term_agent.config import AppConfig, read_config, write_config
from term_agent.modes import ManualMode
from term_agent.ui import ConsoleUI
from term_agent.executor import CommandExecutor
from term_agent.tasks import AgentEngine


def run_manual(config: AppConfig) -> None:
    def should_exit(text: str | None) -> bool:
        return not text or text.strip() == "\\q"

    def parse_manual_command(text: str) -> str | None:
        if not text:
            return None
        stripped = text.lstrip()
        if not stripped.startswith("@"):
            return None
        command = stripped[1:].strip()
        return command or None

    ui = ConsoleUI()
    manual = ManualMode(config)
    executor = CommandExecutor()
    print("Hint: use @ to run a manual command, use \\q to quit.")
    user_input = ui.get_prompt(executor.cwd, executor.conda_env)
    while True:
        if should_exit(user_input):
            return
        manual_command = parse_manual_command(user_input)
        if manual_command:
            manual.record_user_query(user_input)
            execution = executor.execute(manual_command)
            manual.record_command_result(
                command=manual_command,
                return_code=execution.returncode,
                stdout=execution.stdout,
                stderr=execution.stderr,
                cwd=execution.cwd,
            )
            user_input = ui.get_prompt(executor.cwd, executor.conda_env)
            continue
        result = manual.suggest(user_input, executor.cwd)
        ui.show_suggestions(result.suggestions)
        selected = ui.choose_command(result.suggestions)
        if not selected:
            manual.record_dismiss_request(result.suggestions)
            user_input = ui.get_prompt(executor.cwd, executor.conda_env)
            if should_exit(user_input):
                return
            continue
        if selected == ConsoleUI.REGENERATE_CHOICE:
            manual.record_regenerate_request(result.suggestions)
            continue
        execution = executor.execute(selected)
        manual.record_command_result(
            command=selected,
            return_code=execution.returncode,
            stdout=execution.stdout,
            stderr=execution.stderr,
            cwd=execution.cwd,
        )
        user_input = ui.get_prompt(executor.cwd, executor.conda_env)
        if should_exit(user_input):
            return


def run_auto(config: AppConfig) -> None:
    ui = ConsoleUI()
    engine = AgentEngine(config)
    print("Hint: use @ to run a manual command, use \\q to quit.")
    user_input = ui.get_prompt(os.getcwd())
    if not user_input:
        return
    engine.run(user_input)


def print_help_text() -> None:
    text = """
usage: term [-h|--help] <command> [<args>]

These are common TermAgent commands used in various situations:

start a session
   run        Run TermAgent

configure the client
   set        Configure API settings

learn and help
   help       Show help information

The subcommands have their own options:

run
   -m, --manual        Manually pick commands
   -a, --auto          Execute tasks automatically

set
   --api-base          Set API base URL
   --api-key           Set API key
   --model             Set model name
   --temperature       Set temperature

help
   Show this help page

Hint: use @ to run a manual command, use \\q to quit.
""".strip()
    print(text)


def main() -> None:
    if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
        print_help_text()
        return
    parser = argparse.ArgumentParser(
        prog="term",
        description="TermAgent: interactive terminal assistant",
        epilog="Hint: use @ to run a manual command, use \\q to quit. Use `term help` for help.",
    )
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run", help="Run TermAgent")
    run_parser.add_argument("-m", "--manual", action="store_true", help="Manually pick commands")
    run_parser.add_argument("-a", "--auto", action="store_true", help="Execute tasks automatically")
    set_parser = subparsers.add_parser("set", help="Configure API settings")
    set_parser.add_argument("--api-base")
    set_parser.add_argument("--api-key")
    set_parser.add_argument("--model")
    set_parser.add_argument("--temperature", type=float)
    subparsers.add_parser("help", help="Show help information")
    args = parser.parse_args()
    if args.command in {None, "help"}:
        print_help_text()
        return
    if args.command == "set":
        persisted = read_config()
        updates = {
            "api_base": args.api_base,
            "api_key": args.api_key,
            "model": args.model,
            "temperature": args.temperature,
        }
        for key, value in updates.items():
            if value is not None:
                persisted[key] = value
        write_config(persisted)
        return
    config = AppConfig.load()
    if not config.api_key:
        print("API key not found. Run: term set --api-key YOUR_KEY")
        return
    if args.command != "run":
        print_help_text()
        return
    if args.manual and args.auto:
        print("Choose only one of -m or -a")
        return
    if args.auto:
        run_auto(config)
        return
    run_manual(config)


if __name__ == "__main__":
    main()
