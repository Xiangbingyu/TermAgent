import os
from dataclasses import dataclass

from term_agent.executor.shell_platform import strip_wrapping_quotes


@dataclass(frozen=True)
class DirectoryChangeResult:
    cwd: str
    returncode: int
    stdout: str
    stderr: str


def is_change_directory_command(command: str) -> bool:
    lowered = command.lower()
    return lowered.startswith("cd") and (
        len(lowered) == 2 or lowered[2] in {" ", "\t", "\\", "/", "."}
    )


def change_directory(command: str, current_cwd: str) -> DirectoryChangeResult:
    target = command[2:].strip()
    if target.lower().startswith("/d"):
        target = target[2:].strip()
    target = strip_wrapping_quotes(target)
    if not target:
        next_cwd = os.path.expanduser("~")
        output = f"{next_cwd}\n"
        return DirectoryChangeResult(
            cwd=next_cwd,
            returncode=0,
            stdout=output,
            stderr="",
        )
    target = os.path.expanduser(target)
    if not os.path.isabs(target):
        target = os.path.abspath(os.path.join(current_cwd, target))
    if not os.path.isdir(target):
        message = f"Directory not found: {target}\n"
        return DirectoryChangeResult(
            cwd=current_cwd,
            returncode=1,
            stdout="",
            stderr=message,
        )
    output = f"{target}\n"
    return DirectoryChangeResult(
        cwd=target,
        returncode=0,
        stdout=output,
        stderr="",
    )
