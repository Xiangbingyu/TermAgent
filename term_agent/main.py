import argparse
import sys

from term_agent.config import AppConfig, read_config, write_config
from term_agent.modes import ManualMode
from term_agent.ui import ConsoleUI
from term_agent.executor import CommandExecutor
from term_agent.tasks import AgentEngine


def run_manual(config: AppConfig, user_input: str | None) -> None:
    ui = ConsoleUI()
    manual = ManualMode(config)
    executor = CommandExecutor()
    if not user_input:
        user_input = ui.get_prompt()
    if not user_input:
        return
    while True:
        result = manual.suggest(user_input)
        ui.show_reply(result.reply)
        ui.show_suggestions(result.suggestions)
        selected = ui.choose_command(result.suggestions)
        if not selected:
            return
        if selected == ConsoleUI.REGENERATE_CHOICE:
            continue
        executor.run(selected)
        return


def run_auto(config: AppConfig, user_input: str | None) -> None:
    ui = ConsoleUI()
    engine = AgentEngine(config)
    if not user_input:
        user_input = ui.get_prompt()
    if not user_input:
        return
    engine.run(user_input)


def main() -> None:
    if sys.argv[1:2] == ["set"]:
        set_parser = argparse.ArgumentParser()
        set_parser.add_argument("--api-base")
        set_parser.add_argument("--api-key")
        set_parser.add_argument("--model")
        set_parser.add_argument("--temperature", type=float)
        args = set_parser.parse_args(sys.argv[2:])
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
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--manual", action="store_true")
    parser.add_argument("-a", "--auto", action="store_true")
    parser.add_argument("prompt", nargs="*")
    args, unknown = parser.parse_known_args()
    tokens = []
    if args.prompt:
        tokens.extend(args.prompt)
    if unknown:
        tokens.extend(unknown)
    user_input = " ".join(tokens).strip() if tokens else None
    config = AppConfig.load()
    if not config.api_key:
        print("API key not found. Run: term set --api-key YOUR_KEY")
        return
    if args.auto:
        run_auto(config, user_input)
        return
    if args.manual:
        run_manual(config, user_input)
        return
    if not args.auto and not args.manual:
        run_manual(config, user_input)


if __name__ == "__main__":
    main()
