"""Image generation handler — Gemini 2.0 Flash (primary) with AI Horde fallback."""
import logging
import asyncio
import json
import base64
import urllib.request

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

# ── AI Horde Fallback Config ──────────────────
HORDE_API = "https://stablehorde.net/api/v2"
HORDE_KEY = "0000000000"  # Anonymous key


# ── Gemini Image Generation ────────
# Model names to try in order (some may be deprecated/renamed)
_GEMINI_IMAGE_MODELS = [
    "gemini-2.0-flash-preview-image-generation",
    "gemini-2.0-flash-exp-image-generation",
    "imagen-3.0-generate-001",
]

# ── Prompt language helpers ──────────
_UZ_HINTS = {"o'", "g'", "o'z", "bo'", "va ", "bilan", "ham ", "uchun", "deb", "yoz"}

def _build_english_prompt(prompt_text: str, template: str) -> str:
    """Wrap user prompt in high quality instruction. Auto-translate CIS/Uzbek lang prompts."""
    # Detect Cyrillic characters
    has_cyrillic = any('\u0400' <= c <= '\u04ff' for c in prompt_text)
    # Detect Uzbek Latin (common apostrophe combinations like o' g')
    lower = prompt_text.lower()
    has_uzbek_latin = any(hint in lower for hint in _UZ_HINTS)

    if has_cyrillic or has_uzbek_latin:
        return (
            f"Generate a high-quality, detailed, photorealistic image. "
            f"The subject is: '{prompt_text}' (this may be in Uzbek or Russian — interpret it correctly). "
            f"Style: professional photography, sharp focus, vivid colors, 4K quality, no text."
        )
    try:
        final = template.format(prompt=prompt_text)
    except (KeyError, IndexError):
        final = prompt_text
    return final + ", high quality, detailed, photorealistic, 4K, sharp focus, no watermark"


def _try_gemini_image_model(api_key: str, model_name: str, prompt_text: str) -> bytes:
    """Try generating image with a specific Gemini model name."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = json.dumps({
        "contents": [{
            "parts": [{"text": f"Generate an image: {prompt_text}"}]
        }],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
        }
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
    })

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())

    # Extract image from response
    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            if "inlineData" in part:
                img_data = part["inlineData"]
                if img_data.get("data"):
                    return base64.b64decode(img_data["data"])

    raise ValueError(f"Model {model_name} rasm qaytarmadi")


def _generate_gemini_image(prompt_text: str) -> bytes:
    """Generate image via Gemini — tries GEMINIGEN_API_KEY first, then GEMINI_API_KEY."""
    # Prefer GEMINIGEN_API_KEY (AIzaSy... format — real Google Gemini key)
    api_key = settings.GEMINIGEN_API_KEY or settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI API key not configured")
    if api_key.startswith("AQ.") or "." in api_key[:4]:
        # This is NOT a Google API key — skip Gemini
        raise ValueError(f"API key format invalid for Gemini image generation (starts with '{api_key[:6]}')")

    last_error = None
    for model_name in _GEMINI_IMAGE_MODELS:
        try:
            logger.info(f"Gemini Image: trying model '{model_name}'")
            result = _try_gemini_image_model(api_key, model_name, prompt_text)
            logger.info(f"Gemini Image: success with model '{model_name}'")
            return result
        except Exception as e:
            error_str = str(e)
            logger.warning(f"Gemini Image: model '{model_name}' failed: {error_str[:100]}")
            last_error = e
            # Only continue if it's a model-not-found / not-supported error
            if "404" in error_str or "not found" in error_str.lower() or "invalid" in error_str.lower() or "not supported" in error_str.lower():
                continue
            # For other errors (quota, auth, etc.) — re-raise immediately
            raise

    raise ValueError(f"Barcha Gemini modellari muvaffaqiyatsiz: {last_error}")


# ── AI Horde Fallback ─────────────────────────
def _submit_horde_job(prompt_text: str) -> str:
    """Submit image generation job to AI Horde. Returns job ID."""
    url = f"{HORDE_API}/generate/async"
    payload = json.dumps({
        "prompt": prompt_text,
        "params": {"width": 512, "height": 512, "steps": 25, "cfg_scale": 7},
        "nsfw": False,
        "censor_nsfw": False,
        "models": ["stable_diffusion"],
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "apikey": HORDE_KEY,
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        return data["id"]


def _check_horde_job(job_id: str) -> dict:
    url = f"{HORDE_API}/generate/status/{job_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "TelegramBot/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _download_url(img_url: str) -> bytes:
    req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


# ── FSM States ────────────────────────────────
class ImageGenStates(StatesGroup):
    waiting_prompt = State()


# ── Prompt handler ────────────────────────────
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
        "🎨 Surat tayyorlanmoqda... ⏳\nBu 10-30 soniya vaqt olishi mumkin.",
        parse_mode="HTML",
    )

    try:
        # Load custom prompt suffix from DB
        prompt_template = "{prompt}, high quality, detailed, photorealistic"
        try:
            from db.models import AdminSetting
            from sqlalchemy import select as sel
            async with async_session() as db:
                r = await db.execute(sel(AdminSetting.value).where(AdminSetting.key == "prompt_imagegen"))
                custom_tmpl = r.scalar_one_or_none()
                if custom_tmpl:
                    prompt_template = custom_tmpl
        except Exception:
            pass

        # ── Build final prompt ────────────────────────────
        prompt_template = "{prompt}"
        try:
            from db.models import AdminSetting
            from sqlalchemy import select as sel
            async with async_session() as db:
                r = await db.execute(sel(AdminSetting.value).where(AdminSetting.key == "prompt_imagegen"))
                custom_tmpl = r.scalar_one_or_none()
                if custom_tmpl:
                    prompt_template = custom_tmpl
        except Exception:
            pass

        final_prompt = _build_english_prompt(prompt, prompt_template)
        logger.info(f"imagegen final_prompt: {final_prompt[:120]}")

        image_data = None
        used_api = None

        # Try Gemini first (primary — uses GEMINIGEN_API_KEY = AIzaSy... format)
        gemini_key = settings.GEMINIGEN_API_KEY or settings.GEMINI_API_KEY
        if gemini_key and not gemini_key.startswith("AQ."):
            try:
                image_data = await asyncio.to_thread(_generate_gemini_image, final_prompt)
                used_api = "Gemini"
                logger.info(f"Gemini Image: success, {len(image_data)} bytes")
            except Exception as e:
                logger.warning(f"Gemini Image failed: {str(e)[:150]}, falling back to AI Horde")

        # Fallback to AI Horde
        if not image_data:
            logger.info(f"AI Horde: submitting '{final_prompt[:50]}...'")
            used_api = "AI Horde"
            job_id = await asyncio.to_thread(_submit_horde_job, final_prompt)

            for i in range(24):  # max 2 min
                await asyncio.sleep(5)
                result = await asyncio.to_thread(_check_horde_job, job_id)

                if result.get("done"):
                    generations = result.get("generations", [])
                    if generations and generations[0].get("img"):
                        img_url = generations[0]["img"]
                        image_data = await asyncio.to_thread(_download_url, img_url)
                        break
                    else:
                        raise Exception("Surat generatsiya bo'lmadi")

                # Update wait info
                wait = result.get("wait_time", 0)
                queue = result.get("queue_position", 0)
                if i % 3 == 2:
                    try:
                        await status_msg.edit_text(
                            f"🎨 Surat tayyorlanmoqda... ⏳\n"
                            f"⏱ Kutish: ~{wait}s | 📊 Navbat: {queue}"
                        )
                    except Exception:
                        pass

        if not image_data:
            # Timeout — refund
            async with async_session() as session:
                await add_tokens_async(session, message.from_user.id, IMAGE_COST)
                await session.commit()
            await state.clear()
            try:
                await status_msg.edit_text("⏰ Vaqt tugadi. Token qaytarildi. Qayta urinib ko'ring.")
            except Exception:
                pass
            return

        # Success! Send the image
        photo = BufferedInputFile(image_data, filename="image.png")
        async with async_session() as session:
            tokens = await get_tokens_async(session, message.from_user.id)
        await message.answer_photo(
            photo=photo,
            caption=uz.IMAGEGEN_SUCCESS.format(
                prompt=prompt[:200],
                tokens=tokens,
            ),
            parse_mode="HTML",
        )
        try:
            await status_msg.delete()
        except Exception:
            pass

        await state.clear()

        # Ask for more
        await message.answer(
            "Yana xizmat kerakmi? 👇",
            reply_markup=ai_workers_reply_keyboard(),
        )

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
        # Refund tokens on error
        async with async_session() as session:
            await add_tokens_async(session, message.from_user.id, IMAGE_COST)
            await session.commit()
        error_name = type(e).__name__
        error_msg = str(e)[:200]
        logger.error(f"imagegen failed: {error_name}: {error_msg}")
        await state.clear()
        try:
            await status_msg.edit_text(
                f"❌ Xatolik: {error_name}: {error_msg}\n\nToken qaytarildi."
            )
        except Exception:
            pass
