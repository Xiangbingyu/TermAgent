import os
import subprocess
import sys
from dataclasses import dataclass

from term_agent.executor.conda_runtime import (
    activate_conda_environment,
    get_conda_activate_target,
    is_conda_deactivate_command,
)
from term_agent.executor.directory_runtime import (
    change_directory,
    is_change_directory_command,
)
from term_agent.executor.shell_platform import (
    build_shell_args,
    resolve_shell_command,
)


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
        self.python_prefix = os.path.abspath(sys.executable)
        self._default_python_prefix = self.python_prefix
        self._base_env = os.environ.copy()
        self._active_env = self._base_env.copy()
        self.shell_command = resolve_shell_command()

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
        if is_change_directory_command(normalized):
            return self._change_directory(normalized)
        conda_target = get_conda_activate_target(normalized)
        if conda_target is not None:
            return self._activate_conda_environment(normalized, conda_target)
        if is_conda_deactivate_command(normalized):
            self._active_env = self._base_env.copy()
            self.python_prefix = self._default_python_prefix
            return CommandExecutionResult(
                command=normalized,
                cwd=self.cwd,
                returncode=0,
                stdout="",
                stderr="",
            )
        process = subprocess.Popen(
            build_shell_args(self.shell_command, normalized),
            cwd=self.cwd,
            env=self._active_env,
        )
        returncode = process.wait()
        return CommandExecutionResult(
            command=normalized,
            cwd=self.cwd,
            returncode=returncode,
            stdout="(output streamed directly to terminal; not captured)",
            stderr="",
        )

    def _activate_conda_environment(
        self, command: str, target: str
    ) -> CommandExecutionResult:
        activation = activate_conda_environment(
            target=target,
            shell_command=self.shell_command,
            cwd=self.cwd,
            base_env=self._base_env,
        )
        if activation.active_env is not None:
            self._active_env = activation.active_env
        if activation.python_prefix is not None:
            self.python_prefix = activation.python_prefix
        if activation.stdout:
            print(activation.stdout, end="")
        if activation.stderr:
            print(activation.stderr, end="")
        return CommandExecutionResult(
            command=command,
            cwd=self.cwd,
            returncode=activation.returncode,
            stdout=activation.stdout,
            stderr=activation.stderr,
        )

    def _change_directory(self, command: str) -> CommandExecutionResult:
        result = change_directory(command, self.cwd)
        self.cwd = result.cwd
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="")
        return CommandExecutionResult(
            command=command,
            cwd=self.cwd,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
