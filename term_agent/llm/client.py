from langchain_openai import ChatOpenAI
from term_agent.config import AppConfig


def build_chat_model(config: AppConfig) -> ChatOpenAI:
    return ChatOpenAI(
        model=config.model,
        temperature=config.temperature,
        api_key=config.api_key,
        base_url=config.api_base,
    )
