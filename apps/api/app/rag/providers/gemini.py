import asyncio

from google import genai
from google.genai import types


class GeminiChatModel:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
            ),
        )

        if not response.text:
            raise RuntimeError("The model returned an empty response.")

        return response.text
