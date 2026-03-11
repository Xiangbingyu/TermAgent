import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandExecutionResult:
    command: str
    cwd: str
    returncode: int
    stdout: str
    stderr: str


class CommandExecutor:
    def __init__(self) -> None:
        self.cwd = os.getcwd()

    def run(self, command: str) -> int:
        return self.execute(command).returncode

    def execute(self, command: str) -> CommandExecutionResult:
        normalized = command.strip()
        if not normalized:
            return CommandExecutionResult(
                command=normalized,
                cwd=self.cwd,
                returncode=0,
                stdout="",
                stderr="",
            )
        if self._is_change_directory_command(normalized):
            return self._change_directory(normalized)
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", normalized],
            cwd=self.cwd,
            text=True,
            capture_output=True,
        )
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="")
        return CommandExecutionResult(
            command=normalized,
            cwd=self.cwd,
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
        )

    def _is_change_directory_command(self, command: str) -> bool:
        lowered = command.lower()
        return lowered.startswith("cd") and (
            len(lowered) == 2 or lowered[2] in {" ", "\t", "\\", "/", "."}
        )

    def _change_directory(self, command: str) -> CommandExecutionResult:
        target = command[2:].strip()
        if target.lower().startswith("/d"):
            target = target[2:].strip()
        if target.startswith('"') and target.endswith('"') and len(target) >= 2:
            target = target[1:-1]
        if not target:
            self.cwd = os.path.expanduser("~")
            print(self.cwd)
            return CommandExecutionResult(
                command=command,
                cwd=self.cwd,
                returncode=0,
                stdout=f"{self.cwd}\n",
                stderr="",
            )
        target = os.path.expanduser(target)
        if not os.path.isabs(target):
            target = os.path.abspath(os.path.join(self.cwd, target))
        if not os.path.isdir(target):
            message = f"目录不存在: {target}\n"
            print(message, end="")
            return CommandExecutionResult(
                command=command,
                cwd=self.cwd,
                returncode=1,
                stdout="",
                stderr=message,
            )
        self.cwd = target
        print(self.cwd)
        return CommandExecutionResult(
            command=command,
            cwd=self.cwd,
            returncode=0,
            stdout=f"{self.cwd}\n",
            stderr="",
        )
