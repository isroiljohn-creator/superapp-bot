"""Gemini AI moduli — Nuvi Jobs uchun soddalashtirilgan shaklda."""

from __future__ import annotations
import logging
import google.generativeai as genai

logger = logging.getLogger("jarvis.ai")

class GeminiAI:
    """Gemini 2.5 Flash yordamida oddiy matn generatsiyasi."""

    def __init__(self, api_key: str) -> None:
        genai.configure(api_key=api_key)
        logger.info("✅ Gemini AI tayyorlandi.")

    async def process_message(
        self,
        prompt: str,
        system_prompt: str,
        tool_executor = None,
        images: list[tuple[str, bytes]] | None = None,
        use_tools: bool = False,
    ) -> str | None:
        """Xabarni qayta ishlash. Xato holida None qaytaradi — chaqiruvchi
        buni haqiqiy (lekin bo'sh) AI javobidan farqlab, doimiy "rad etilgan"
        deb belgilashdan saqlanishi kerak (masalan kvota tugagan bo'lsa,
        keyinroq qayta urinib ko'rish imkoni qolishi uchun)."""
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_prompt or None,
                generation_config={"temperature": 0.5, "max_output_tokens": 8192},
            )
            response = await model.generate_content_async(prompt)
            if response and response.text:
                return response.text.strip()
            return "..."
        except Exception as e:
            logger.error(f"Gemini xatosi: {e}")
            return None
