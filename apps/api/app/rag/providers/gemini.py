import asyncio

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
            raise ChatModelError("Gemini failed to generate an answer.") from exc

        if not response.text:
            raise ChatModelError("Gemini returned an empty answer.")

        return response.text
