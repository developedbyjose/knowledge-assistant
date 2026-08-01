from collections.abc import AsyncIterator
from typing import Protocol


class ChatModelError(RuntimeError):
    """Raised when a chat model provider cannot produce an answer."""


class ChatModel(Protocol):
    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        ...

    def stream_generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        ...
