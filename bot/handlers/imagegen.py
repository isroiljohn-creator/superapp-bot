"""Image generation handler — GeminiGen AI (primary) with AI Horde fallback."""
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
from bot.keyboards.buttons import main_menu_keyboard, ai_workers_reply_keyboard
from db.database import async_session
from services.token_service import spend_tokens_async, get_tokens_async, add_tokens_async, IMAGE_COST

router = Router(name="imagegen")
logger = logging.getLogger("imagegen")

# ── GeminiGen API Config ──────────────────────
GEMINIGEN_API = "https://api.geminigen.ai/uapi/v1/generate_image"
GEMINIGEN_MODEL = "nano-banana-pro"

# ── AI Horde Fallback Config ──────────────────
HORDE_API = "https://stablehorde.net/api/v2"
HORDE_KEY = "0000000000"  # Anonymous key


# ── GeminiGen API (Primary) ──────────────────
def _generate_geminigen(prompt_text: str) -> bytes:
    """Generate image via GeminiGen API. Returns image bytes."""
    api_key = settings.GEMINIGEN_API_KEY
    if not api_key:
        raise ValueError("GEMINIGEN_API_KEY not configured")

    # Build multipart form data
    import io
    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    
    body_parts = []
    # prompt field
    body_parts.append(f"--{boundary}")
    body_parts.append('Content-Disposition: form-data; name="prompt"')
    body_parts.append("")
    body_parts.append(prompt_text)
    # model field
    body_parts.append(f"--{boundary}")
    body_parts.append('Content-Disposition: form-data; name="model"')
    body_parts.append("")
    body_parts.append(GEMINIGEN_MODEL)
    # aspect_ratio field
    body_parts.append(f"--{boundary}")
    body_parts.append('Content-Disposition: form-data; name="aspect_ratio"')
    body_parts.append("")
    body_parts.append("1:1")
    # style field
    body_parts.append(f"--{boundary}")
    body_parts.append('Content-Disposition: form-data; name="style"')
    body_parts.append("")
    body_parts.append("photorealistic")
    # end boundary
    body_parts.append(f"--{boundary}--")
    body_parts.append("")
    
    body = "\r\n".join(body_parts).encode("utf-8")
    
    req = urllib.request.Request(GEMINIGEN_API, data=body, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "x-api-key": api_key,
        "Accept": "application/json",
    })
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    
    # Try to get image from response
    # Option 1: base64_images field (demo format)
    if "base64_images" in data:
        b64 = data["base64_images"]
        if isinstance(b64, list):
            b64 = b64[0]
        # Strip data URI prefix if present
        if "," in b64:
            b64 = b64.split(",", 1)[1]
        return base64.b64decode(b64)
    
    # Option 2: generate_result field (URL format)
    if "generate_result" in data:
        img_url = data["generate_result"]
        return _download_url(img_url)
    
    # Option 3: image_url field
    if "image_url" in data:
        return _download_url(data["image_url"])
    
    raise ValueError(f"Unexpected API response: {list(data.keys())}")


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
        uz.MENU_BTN_COURSE, uz.MENU_BTN_PROFILE,
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
                reply_markup=main_menu_keyboard(user_id=message.from_user.id),
            )
            return
        await session.commit()

    status_msg = await message.answer(
        "🎨 Surat tayyorlanmoqda... ⏳\nBu 10-30 soniya vaqt olishi mumkin.",
        parse_mode="HTML",
    )

    try:
        # Add quality hint for non-Latin prompts
        if any(ord(c) > 127 for c in prompt):
            final_prompt = f"{prompt}, high quality, detailed, photorealistic"
        else:
            final_prompt = prompt

        image_data = None
        used_api = None

        # Try GeminiGen first (primary)
        if settings.GEMINIGEN_API_KEY:
            try:
                logger.info(f"GeminiGen: generating '{final_prompt[:50]}...'")
                image_data = await asyncio.to_thread(_generate_geminigen, final_prompt)
                used_api = "GeminiGen"
                logger.info(f"GeminiGen: success, {len(image_data)} bytes")
            except Exception as e:
                logger.warning(f"GeminiGen failed: {e}, falling back to AI Horde")

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
            try:
                await status_msg.edit_text("⏰ Vaqt tugadi. Token qaytarildi. Qayta urinib ko'ring.")
            except Exception:
                pass
            return

        # Success! Send the image
        photo = BufferedInputFile(image_data, filename="image.jpg")
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
