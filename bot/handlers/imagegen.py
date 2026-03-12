"""Image generation handler — AI Horde (free, no API key) with token system."""
import logging
import asyncio
import json
import urllib.parse
import urllib.request

from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.locales import uz
from bot.keyboards.buttons import main_menu_keyboard
from services.token_service import spend_tokens, get_tokens, add_tokens, IMAGE_COST

router = Router(name="imagegen")
logger = logging.getLogger("imagegen")

# ── Config ────────────────────────────────────
HORDE_API = "https://stablehorde.net/api/v2"
HORDE_KEY = "0000000000"  # Anonymous key — free, no registration


def _submit_job(prompt_text: str) -> str:
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


def _check_job(job_id: str) -> dict:
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
        uz.MENU_BTN_AI_WORKERS, uz.MENU_BTN_CLUB, uz.MENU_BTN_COURSE,
        uz.MENU_BTN_LESSONS, uz.MENU_BTN_REFERRAL, uz.MENU_BTN_GUIDES,
        uz.MENU_BTN_HELP,
    ]
    if prompt in menu_buttons:
        await state.clear()
        return

    # Spend tokens
    if not spend_tokens(message.from_user.id, IMAGE_COST):
        tokens = get_tokens(message.from_user.id)
        await state.clear()
        await message.answer(
            uz.AI_WORKERS_NO_TOKENS.format(needed=IMAGE_COST, have=tokens),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(user_id=message.from_user.id),
        )
        return

    status_msg = await message.answer(
        "🎨 Surat tayyorlanmoqda... ⏳\nBu 20-60 soniya vaqt olishi mumkin.",
        parse_mode="HTML",
    )

    try:
        # Add quality hint for non-Latin prompts
        if any(ord(c) > 127 for c in prompt):
            final_prompt = f"{prompt}, high quality, detailed"
        else:
            final_prompt = prompt

        logger.info(f"Submitting job: {final_prompt}")
        job_id = await asyncio.to_thread(_submit_job, final_prompt)

        # Poll for completion (max 2 min)
        for i in range(24):
            await asyncio.sleep(5)
            result = await asyncio.to_thread(_check_job, job_id)

            if result.get("done"):
                generations = result.get("generations", [])
                if generations and generations[0].get("img"):
                    img_url = generations[0]["img"]
                    image_data = await asyncio.to_thread(_download_url, img_url)

                    photo = BufferedInputFile(image_data, filename="image.jpg")
                    tokens = get_tokens(message.from_user.id)
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
                    from bot.handlers.ai_workers import ai_workers_keyboard
                    await message.answer(
                        "Yana xizmat kerakmi? 👇",
                        reply_markup=ai_workers_keyboard(message.from_user.id),
                    )

                    # Analytics
                    try:
                        from db.database import async_session
                        from services.analytics import AnalyticsService
                        from services.crm import CRMService
                        async with async_session() as db:
                            crm = CRMService(db)
                            user = await crm.get_user(message.from_user.id)
                            if user:
                                analytics = AnalyticsService(db)
                                await analytics.track(user_id=user.id, event_type="imagegen_free")
                                await db.commit()
                    except Exception:
                        pass
                    return
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

        # Timeout — refund
        add_tokens(message.from_user.id, IMAGE_COST)
        try:
            await status_msg.edit_text("⏰ Vaqt tugadi. Token qaytarildi. Qayta urinib ko'ring.")
        except Exception:
            pass

    except Exception as e:
        # Refund tokens on error
        add_tokens(message.from_user.id, IMAGE_COST)
        error_name = type(e).__name__
        error_msg = str(e)[:200]
        logger.error(f"imagegen failed: {error_name}: {error_msg}")
        try:
            await status_msg.edit_text(
                f"❌ Xatolik: {error_name}: {error_msg}\n\nToken qaytarildi."
            )
        except Exception:
            pass
