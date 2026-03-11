from langchain_core.prompts import ChatPromptTemplate


def manual_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a terminal command expert. Output only a JSON array of string commands, and no other text.",
            ),
            ("human", "{user_input}"),
        ]
    )
