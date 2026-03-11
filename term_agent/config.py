from dataclasses import dataclass
import json
import os


def _config_path() -> str:
    if os.name == "nt":
        base = os.path.expanduser("~")
        return os.path.join(base, "AppData", "Roaming", "term-agent", "config.json")
    return os.path.expanduser("~/.config/term-agent/config.json")


def read_config() -> dict:
    path = _config_path()
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def write_config(data: dict) -> None:
    path = _config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


@dataclass(frozen=True)
class AppConfig:
    api_base: str
    api_key: str
    model: str
    temperature: float

    @staticmethod
    def load() -> "AppConfig":
        persisted = read_config()
        api_base = (
            persisted.get("api_base")
            or "https://api.openai.com/v1"
        )
        api_key = (
            persisted.get("api_key")
            or ""
        )
        model = (
            persisted.get("model")
            or "gpt-4o-mini"
        )
        temperature = float(
            persisted.get("temperature")
            or "0.2"
        )
        return AppConfig(
            api_base=api_base,
            api_key=api_key,
            model=model,
            temperature=temperature,
        )
