from langchain_core.prompts import ChatPromptTemplate


def auto_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a terminal automation assistant. Output a JSON object with action and command fields.",
            ),
            ("human", "{user_input}"),
        ]
    )
