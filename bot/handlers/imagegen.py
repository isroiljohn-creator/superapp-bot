"""Image generation handler.

Priority:
  1. Pollinations.ai  — FREE, FLUX model, HIGH quality (no API key needed)
  2. Gemini 2.0 Flash — Google AI (fallback)
  3. AI Horde         — Last resort (very slow & low quality)
"""
import logging
import asyncio
import json
import base64
import urllib.request
import urllib.parse

from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.locales import uz
from bot.config import settings
from bot.keyboards.buttons import get_main_menu, ai_workers_reply_keyboard
from db.database import async_session
from services.token_service import spend_tokens_async, get_tokens_async, add_tokens_async, IMAGE_COST

router = Router(name="imagegen")
logger = logging.getLogger("imagegen")

# ── AI Horde Last-Resort Config ───────────────
HORDE_API = "https://stablehorde.net/api/v2"
HORDE_KEY = "0000000000"  # Anonymous key

# ── Language detection helpers ────────────────
_UZ_HINTS = {"o'", "g'", "o'z", "bo'", "va ", "bilan", "ham ", "uchun", "deb", "yoz"}


def _build_english_prompt(prompt_text: str) -> str:
    """Convert Uzbek/Russian prompt into a clean English generation prompt."""
    has_cyrillic = any('\u0400' <= c <= '\u04ff' for c in prompt_text)
    lower = prompt_text.lower()
    has_uzbek_latin = any(hint in lower for hint in _UZ_HINTS)

    if has_cyrillic or has_uzbek_latin:
        # Wrap with explicit translation instruction
        return (
            f"photorealistic image of: {prompt_text} "
            f"(subject described in Uzbek or Russian, render visually), "
            f"ultra detailed, 4K, sharp focus, professional photography, vivid colors, no text"
        )
    return (
        f"{prompt_text}, ultra detailed, 4K, sharp focus, "
        f"professional photography, vivid colors, photorealistic, no text, no watermark"
    )


# ══════════════════════════════════════════════
# 1. PRIMARY: Gemini Image Generation (Nano Banana)
# ══════════════════════════════════════════════
_GEMINI_IMAGE_MODELS = [
    "nano-banana-pro-preview",
    "gemini-3.1-flash-image-preview",
    "gemini-2.5-flash-image",
    "gemini-3-pro-image-preview",
    "imagen-4.0-generate-001",
]

def _try_gemini_image_model(api_key: str, model_name: str, prompt_text: str) -> bytes:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={api_key}"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": f"Generate an image: {prompt_text}"}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part and part["inlineData"].get("data"):
            return base64.b64decode(part["inlineData"]["data"])
    raise ValueError(f"Model {model_name} returned no image")


def _generate_gemini_image(prompt_text: str) -> bytes:
    api_key = settings.GEMINIGEN_API_KEY or settings.GEMINI_API_KEY
    if not api_key or not api_key.startswith("AIza"):
        raise ValueError("Valid Google Gemini API key (AIzaSy...) not configured")
    last_error = None
    for model_name in _GEMINI_IMAGE_MODELS:
        try:
            logger.info(f"Gemini Image: trying '{model_name}'")
            result = _try_gemini_image_model(api_key, model_name, prompt_text)
            logger.info(f"Gemini Image: success with '{model_name}'")
            return result
        except Exception as e:
            err = str(e)
            logger.warning(f"Gemini Image: '{model_name}' failed: {err[:100]}")
            last_error = e
            if any(k in err.lower() for k in ("404", "not found", "invalid", "not supported")):
                continue
            raise
    raise ValueError(f"All Gemini models failed: {last_error}")


# ══════════════════════════════════════════════
# 2. FALLBACK: Pollinations.ai (FREE, FLUX model)
# ══════════════════════════════════════════════
def _generate_pollinations_image(prompt_text: str, width: int = 1024, height: int = 1024) -> bytes:
    """
    Generate image via Pollinations.ai — completely free, high quality models.
    Tries models in order: flux-realism → turbo → flux
    Returns raw PNG/JPEG bytes.
    """
    # Best quality models in priority order
    models_to_try = ["flux-realism", "turbo", "flux"]

    for model in models_to_try:
        try:
            encoded = urllib.parse.quote(prompt_text)
            url = (
                f"https://image.pollinations.ai/prompt/{encoded}"
                f"?width={width}&height={height}&model={model}"
                f"&nologo=true&enhance=true&seed=-1"
            )
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; TelegramBot/1.0)",
            })
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
            if len(data) < 1000:
                raise ValueError(f"Too small response: {len(data)} bytes")
            logger.info(f"Pollinations '{model}': {len(data):,} bytes")
            return data
        except Exception as e:
            logger.warning(f"Pollinations model '{model}' failed: {str(e)[:80]}, trying next...")
            continue

    raise ValueError("All Pollinations models failed")

# ══════════════════════════════════════════════
# 3. LAST RESORT: AI Horde
# ══════════════════════════════════════════════
def _submit_horde_job(prompt_text: str) -> str:
    url = f"{HORDE_API}/generate/async"
    payload = json.dumps({
        "prompt": prompt_text,
        "params": {"width": 512, "height": 512, "steps": 30, "cfg_scale": 7},
        "nsfw": False, "censor_nsfw": False,
        "models": ["Deliberate"],
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json", "apikey": HORDE_KEY,
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["id"]


def _check_horde_job(job_id: str) -> dict:
    req = urllib.request.Request(
        f"{HORDE_API}/generate/status/{job_id}",
        headers={"User-Agent": "TelegramBot/1.0"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _download_url(img_url: str) -> bytes:
    req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


# ══════════════════════════════════════════════
# FSM States
# ══════════════════════════════════════════════
class ImageGenStates(StatesGroup):
    waiting_prompt = State()


# ══════════════════════════════════════════════
# Main handler
# ══════════════════════════════════════════════
@router.message(ImageGenStates.waiting_prompt, F.text)
async def handle_imagegen_prompt(message: Message, state: FSMContext):
    prompt = message.text.strip()

    # Skip menu buttons
    menu_buttons = [
        uz.MENU_BTN_AI_WORKERS, uz.MENU_BTN_FREE_LESSONS, uz.MENU_BTN_CLUB,
        uz.MENU_BTN_COURSE, uz.MENU_BTN_PROFILE, uz.MENU_BTN_BACK,
        uz.AI_WORKERS_KB_IMAGE, uz.AI_WORKERS_KB_COPY, uz.AI_WORKERS_KB_DAILY,
        uz.AI_WORKERS_KB_CHAT, uz.AI_WORKERS_KB_TOPUP, uz.AI_WORKERS_KB_BACK,
        uz.AI_WORKERS_KB_PRES, uz.AI_WORKERS_KB_LYRICS,
    ]
    if prompt in menu_buttons:
        await state.clear()
        return

    # Spend tokens
    async with async_session() as session:
        if not await spend_tokens_async(session, message.from_user.id, IMAGE_COST):
            tokens = await get_tokens_async(session, message.from_user.id)
            await state.clear()
            await message.answer(
                uz.AI_WORKERS_NO_TOKENS.format(needed=IMAGE_COST, have=tokens),
                parse_mode="HTML",
                reply_markup=await get_main_menu(user_id=message.from_user.id),
            )
            return
        await session.commit()

    status_msg = await message.answer(
        "🎨 Surat tayyorlanmoqda... ⏳\n"
        "Bu 10-30 soniya vaqt olishi mumkin.",
        parse_mode="HTML",
    )

    try:
        # Build optimized English prompt
        final_prompt = _build_english_prompt(prompt)
        logger.info(f"imagegen prompt: {final_prompt[:120]}")

        image_data: bytes | None = None
        used_api: str | None = None

        # ── 1. Gemini (PRIMARY - Nano Banana)
        try:
            await status_msg.edit_text(
                "🎨 Surat tayyorlanmoqda... ⏳\n"
                "✨ Gemini (Nano Banana) orqali yasalmoqda..."
            )
            image_data = await asyncio.to_thread(_generate_gemini_image, final_prompt)
            used_api = "Gemini"
            logger.info(f"Gemini: success, {len(image_data)} bytes")
        except Exception as e:
            logger.warning(f"Gemini failed: {str(e)[:150]}, trying Pollinations...")

        # ── 2. Pollinations.ai (FALLBACK)
        if not image_data:
            try:
                await status_msg.edit_text(
                    "🎨 Surat tayyorlanmoqda... ⏳\n"
                    "🔁 FLUX model bilan generatsiya qilinmoqda..."
                )
                image_data = await asyncio.to_thread(_generate_pollinations_image, final_prompt)
                used_api = "Pollinations (FLUX)"
                logger.info(f"Pollinations: success, {len(image_data)} bytes")
            except Exception as e:
                logger.warning(f"Pollinations failed: {str(e)[:150]}, trying AI Horde...")

        # ── 3. AI Horde (LAST RESORT)
        if not image_data:
            await status_msg.edit_text(
                "🎨 Surat tayyorlanmoqda... ⏳\n"
                "🐢 Navbat kutilmoqda (1-2 daqiqa)..."
            )
            used_api = "AI Horde"
            job_id = await asyncio.to_thread(_submit_horde_job, final_prompt)
            for i in range(30):
                await asyncio.sleep(5)
                result = await asyncio.to_thread(_check_horde_job, job_id)
                if result.get("done"):
                    generations = result.get("generations", [])
                    if generations and generations[0].get("img"):
                        image_data = await asyncio.to_thread(_download_url, generations[0]["img"])
                        break
                    raise Exception("AI Horde: no image in response")
                if i % 3 == 2:
                    try:
                        wait = result.get("wait_time", 0)
                        queue = result.get("queue_position", 0)
                        await status_msg.edit_text(
                            f"🎨 Surat tayyorlanmoqda... ⏳\n"
                            f"⏱ ~{wait}s | 📊 Navbat: {queue}"
                        )
                    except Exception:
                        pass

        # ── Timeout
        if not image_data:
            async with async_session() as session:
                await add_tokens_async(session, message.from_user.id, IMAGE_COST)
                await session.commit()
            await state.clear()
            try:
                await status_msg.edit_text("⏰ Vaqt tugadi. Token qaytarildi. Qayta urinib ko'ring.")
            except Exception:
                pass
            return

        # ── SUCCESS — send image
        photo = BufferedInputFile(image_data, filename="image.png")
        async with async_session() as session:
            tokens = await get_tokens_async(session, message.from_user.id)
        await message.answer_photo(
            photo=photo,
            caption=uz.IMAGEGEN_SUCCESS.format(prompt=prompt[:200], tokens=tokens),
            parse_mode="HTML",
        )
        try:
            await status_msg.delete()
        except Exception:
            pass

        await state.clear()
        await message.answer("Yana xizmat kerakmi? 👇", reply_markup=ai_workers_reply_keyboard())

        # Analytics
        try:
            async with async_session() as db:
                from services.analytics import AnalyticsService
                from services.crm import CRMService
                crm = CRMService(db)
                user = await crm.get_user(message.from_user.id)
                if user:
                    analytics = AnalyticsService(db)
                    await analytics.track(user_id=user.id, event_type="imagegen_free")
                    await db.commit()
        except Exception:
            pass

    except Exception as e:
        try:
            async with async_session() as session:
                await add_tokens_async(session, message.from_user.id, IMAGE_COST)
                await session.commit()
        except Exception as db_err:
            logger.error(f"Failed to refund tokens: {db_err}")
            
        err_msg = str(e)[:200]
        logger.error(f"imagegen failed ({type(e).__name__}): {err_msg}")
        await state.clear()
        try:
            await status_msg.edit_text(
                f"❌ Xatolik yuz berdi: {err_msg}\n\nToken qaytarildi. Qayta urinib ko'ring."
            )
        except Exception:
            pass
