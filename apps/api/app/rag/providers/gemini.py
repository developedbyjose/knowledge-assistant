import asyncio
from collections.abc import AsyncIterator
from threading import Thread
from typing import Union

from google import genai
from google.genai import types

from app.rag.providers.chat import ChatModelError


class GeminiChatModel:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ) -> None:
        if not api_key.strip():
            raise ChatModelError("Gemini API key is not configured.")

        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,
                ),
            )
        except Exception as exc:
            raise ChatModelError(_provider_error("generate an answer", exc)) from exc

        if not response.text:
            raise ChatModelError("Gemini returned an empty answer.")

        return response.text

    async def stream_generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Union[str, Exception, None]] = asyncio.Queue()

        def run_stream() -> None:
            try:
                for chunk in self.client.models.generate_content_stream(
                    model=self.model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.1,
                    ),
                ):
                    text = getattr(chunk, "text", None)
                    if text:
                        loop.call_soon_threadsafe(queue.put_nowait, text)
                loop.call_soon_threadsafe(queue.put_nowait, None)
            except Exception as exc:
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    ChatModelError(_provider_error("stream an answer", exc)),
                )

        Thread(target=run_stream, daemon=True).start()
        emitted = False

        while True:
            item = await queue.get()
            if item is None:
                break
            if isinstance(item, Exception):
                raise item

            emitted = True
            yield item

        if not emitted:
            raise ChatModelError("Gemini returned an empty answer.")


def _provider_error(action: str, exc: Exception) -> str:
    detail = str(exc)
    if "RESOURCE_EXHAUSTED" in detail or "429" in detail:
        return "Gemini quota or rate limit was exceeded. Check the API key billing/quota settings."
    if "NOT_FOUND" in detail or "404" in detail:
        return "Gemini model is unavailable for this API key. Update LLM_MODEL to an available model."
    return f"Gemini failed to {action}: {detail}"
