import os
import subprocess
from dataclasses import dataclass

from term_agent.executor.shell_platform import build_shell_args, strip_wrapping_quotes


@dataclass(frozen=True)
class CondaActivationResult:
    returncode: int
    stdout: str
    stderr: str
    python_prefix: str | None
    active_env: dict[str, str] | None


def get_conda_activate_target(command: str) -> str | None:
    lowered = command.lower()
    if not lowered.startswith("conda activate"):
        return None
    target = command[len("conda activate") :].strip()
    target = strip_wrapping_quotes(target)
    return target or None


def is_conda_deactivate_command(command: str) -> bool:
    lowered = command.lower()
    return lowered == "conda deactivate" or lowered.startswith("conda deactivate ")


def resolve_conda_env_root(
    target: str,
    shell_command: str,
    cwd: str,
    base_env: dict[str, str],
) -> str | None:
    expanded_target = os.path.expanduser(strip_wrapping_quotes(target))
    if os.path.isdir(expanded_target):
        return expanded_target
    base_path = resolve_conda_base_path(shell_command, cwd, base_env)
    if not base_path:
        return None
    if expanded_target.lower() == "base":
        return base_path
    candidate = os.path.join(base_path, "envs", expanded_target)
    if os.path.isdir(candidate):
        return candidate
    return None


def resolve_conda_base_path(
    shell_command: str,
    cwd: str,
    base_env: dict[str, str],
) -> str | None:
    result = subprocess.run(
        build_shell_args(shell_command, "conda info --base"),
        cwd=cwd,
        text=True,
        capture_output=True,
        env=base_env,
    )
    if result.returncode != 0:
        return None
    base_path = (result.stdout or "").strip()
    if not base_path:
        return None
    if not os.path.isdir(base_path):
        return None
    return base_path


def resolve_env_python_executable(env_root: str) -> str | None:
    if os.name == "nt":
        candidate = os.path.join(env_root, "python.exe")
    else:
        candidate = os.path.join(env_root, "bin", "python")
    if os.path.isfile(candidate):
        return candidate
    return None


def build_env_variables(base_env: dict[str, str], env_root: str) -> dict[str, str]:
    env_vars = base_env.copy()
    path_value = env_vars.get("PATH", "")
    if os.name == "nt":
        env_paths = [
            env_root,
            os.path.join(env_root, "Scripts"),
            os.path.join(env_root, "Library", "bin"),
            os.path.join(env_root, "Library", "usr", "bin"),
            os.path.join(env_root, "Library", "mingw-w64", "bin"),
        ]
    else:
        env_paths = [os.path.join(env_root, "bin")]
    filtered_paths = [path for path in env_paths if os.path.isdir(path)]
    env_vars["PATH"] = (
        os.pathsep.join([*filtered_paths, path_value])
        if path_value
        else os.pathsep.join(filtered_paths)
    )
    env_vars["CONDA_PREFIX"] = env_root
    env_vars["VIRTUAL_ENV"] = env_root
    return env_vars


def activate_conda_environment(
    target: str,
    shell_command: str,
    cwd: str,
    base_env: dict[str, str],
) -> CondaActivationResult:
    env_root = resolve_conda_env_root(
        target=target,
        shell_command=shell_command,
        cwd=cwd,
        base_env=base_env,
    )
    if not env_root:
        message = f"Conda environment not found: {target}\n"
        return CondaActivationResult(
            returncode=1,
            stdout="",
            stderr=message,
            python_prefix=None,
            active_env=None,
        )
    python_executable = resolve_env_python_executable(env_root)
    if not python_executable:
        message = f"Python executable not found in environment: {env_root}\n"
        return CondaActivationResult(
            returncode=1,
            stdout="",
            stderr=message,
            python_prefix=None,
            active_env=None,
        )
    active_env = build_env_variables(base_env, env_root)
    output = f"Activated environment python: {python_executable}\n"
    return CondaActivationResult(
        returncode=0,
        stdout=output,
        stderr="",
        python_prefix=python_executable,
        active_env=active_env,
    )
