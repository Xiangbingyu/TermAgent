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
        self.conda_env: str | None = None
        self.shell_command = self._resolve_shell_command()

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
        conda_target = self._get_conda_activate_target(normalized)
        if conda_target is not None:
            self.conda_env = conda_target
            return CommandExecutionResult(
                command=normalized,
                cwd=self.cwd,
                returncode=0,
                stdout="",
                stderr="",
            )
        if self._is_conda_deactivate_command(normalized):
            self.conda_env = None
            return CommandExecutionResult(
                command=normalized,
                cwd=self.cwd,
                returncode=0,
                stdout="",
                stderr="",
            )
        command_to_run = normalized
        if self.conda_env and not normalized.lower().startswith("conda "):
            command_to_run = f'conda run -n "{self.conda_env}" {normalized}'
        result = subprocess.run(
            self._build_shell_args(command_to_run),
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

    def _resolve_shell_command(self) -> str:
        if os.name == "nt":
            return "powershell"
        return os.environ.get("SHELL", "/bin/bash")

    def _build_shell_args(self, command: str) -> list[str]:
        if os.name == "nt":
            return [self.shell_command, "-NoProfile", "-Command", command]
        return [self.shell_command, "-lc", command]

    def _get_conda_activate_target(self, command: str) -> str | None:
        lowered = command.lower()
        if not lowered.startswith("conda activate"):
            return None
        target = command[len("conda activate") :].strip()
        if target.startswith('"') and target.endswith('"') and len(target) >= 2:
            target = target[1:-1]
        return target or None

    def _is_conda_deactivate_command(self, command: str) -> bool:
        lowered = command.lower()
        return lowered == "conda deactivate" or lowered.startswith("conda deactivate ")

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
            message = f"Directory not found: {target}\n"
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
