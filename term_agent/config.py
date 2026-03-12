from dataclasses import dataclass
import json
import os


def _config_path() -> str:
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return os.path.join(appdata, "term-agent", "config.json")
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
        api_base_raw = persisted.get("api_base")
        api_key_raw = persisted.get("api_key")
        model_raw = persisted.get("model")
        temperature_raw = persisted.get("temperature")
        api_base = str(api_base_raw) if api_base_raw else "https://api.openai.com/v1"
        api_key = str(api_key_raw) if api_key_raw else ""
        model = str(model_raw) if model_raw else "gpt-4o-mini"
        temperature = float(temperature_raw) if temperature_raw is not None else 0.2
        return AppConfig(
            api_base=api_base,
            api_key=api_key,
            model=model,
            temperature=temperature,
        )
