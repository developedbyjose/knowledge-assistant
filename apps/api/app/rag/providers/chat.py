from typing import Protocol


class ChatModel(Protocol):
    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        ...
