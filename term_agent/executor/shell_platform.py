import os


def resolve_shell_command() -> str:
    if os.name == "nt":
        return "powershell.exe"
    return os.environ.get("SHELL") or "/bin/bash"


def build_shell_args(shell_command: str, command: str) -> list[str]:
    if os.name == "nt":
        return [shell_command, "-NoProfile", "-Command", command]
    return [shell_command, "-c", command]


def strip_wrapping_quotes(text: str) -> str:
    if len(text) < 2:
        return text
    if (text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'"):
        return text[1:-1]
    return text
