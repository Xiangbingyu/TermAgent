import subprocess


class CommandExecutor:
    def run(self, command: str) -> int:
        result = subprocess.run(command, shell=True)
        return result.returncode
