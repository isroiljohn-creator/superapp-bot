"""Image generation handler — Gemini Nano Banana (primary) + Pollinations fallback, with I2I and ratio/format selection."""
import logging
import asyncio
import json
import base64
import urllib.request
import urllib.parse
from io import BytesIO

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.locales import uz
from bot.config import settings
from bot.keyboards.buttons import get_main_menu, ai_workers_reply_keyboard
from db.database import async_session
from services.token_service import spend_tokens_async, get_tokens_async, add_tokens_async, IMAGE_COST

router = Router(name="imagegen")
logger = logging.getLogger("imagegen")

# ── AI Horde Config ────────
HORDE_API = "https://stablehorde.net/api/v2"
HORDE_KEY = "0000000000"

# ── Language detection ────────
_UZ_HINTS = {"o'", "g'", "o'z", "bo'", "va ", "bilan", "ham ", "uchun", "deb", "yoz"}

def _build_english_prompt(prompt_text: str) -> str:
    has_cyrillic = any('\u0400' <= c <= '\u04ff' for c in prompt_text)
    lower = prompt_text.lower()
    has_uzbek_latin = any(hint in lower for hint in _UZ_HINTS)

    if has_cyrillic or has_uzbek_latin:
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
# 1. PRIMARY: Gemini
# ══════════════════════════════════════════════
_GEMINI_IMAGE_MODELS = [
    "nano-banana-pro-preview",
    "gemini-3.1-flash-image-preview",
    "gemini-2.5-flash-image",
    "gemini-3-pro-image-preview",
    "imagen-4.0-generate-001",
]

def _try_gemini_image_model(api_key: str, model_name: str, prompt_text: str, ratio: str, ref_image: bytes = None) -> bytes:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    parts = [{"text": f"Generate an exact {ratio} aspect ratio image. Prompt: {prompt_text}"}]
    if ref_image:
        parts.append({
            "inlineData": {
                "mimeType": "image/jpeg",
                "data": base64.b64encode(ref_image).decode("utf-8")
            }
        })
        
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            # Some Google models accept string ratios directly
            "temperature": 0.4
        }
    }
    
    # Try adding imageConfig -> aspect_ratio if supported, don't crash if ignored.
    try:
        # Standardize ratio for Gemini (1:1, 16:9, 9:16)
        formatted_ratio = ratio.replace(":", "") if ratio else "11"
        payload["generationConfig"]["imageConfig"] = {"aspectRatio": ratio}
    except Exception:
        pass

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    
    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part and part["inlineData"].get("data"):
            return base64.b64decode(part["inlineData"]["data"])
    raise ValueError(f"Model {model_name} returned no image")

def _generate_gemini_image(prompt_text: str, ratio: str, ref_image: bytes) -> bytes:
    api_key = settings.GEMINIGEN_API_KEY or settings.GEMINI_API_KEY
    if not api_key or not api_key.startswith("AIza"):
        raise ValueError("Valid Google Gemini API key (AIzaSy...) not configured")
    last_error = None
    for model_name in _GEMINI_IMAGE_MODELS:
        try:
            return _try_gemini_image_model(api_key, model_name, prompt_text, ratio, ref_image)
        except Exception as e:
            err = str(e)
            logger.warning(f"Gemini '{model_name}' failed: {err[:100]}")
            last_error = e
            if any(k in err.lower() for k in ("404", "not found", "invalid", "not supported")):
                continue
            raise
    raise ValueError(f"All Gemini models failed: {last_error}")

# ══════════════════════════════════════════════
# 2. FALLBACK: Pollinations
# ══════════════════════════════════════════════
def _generate_pollinations_image(prompt_text: str, ratio: str) -> bytes:
    models_to_try = ["flux-realism", "turbo", "flux"]
    
    width, height = 1024, 1024
    if ratio == "16:9":
        width, height = 1024, 576
    elif ratio == "9:16":
        width, height = 576, 1024

    for model in models_to_try:
        try:
            encoded = urllib.parse.quote(prompt_text)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&model={model}&nologo=true&seed=-1"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
            if len(data) < 1000:
                raise ValueError("Too small response")
            return data
        except Exception as e:
            logger.warning(f"Pollinations '{model}' failed: {e}")
            continue
    raise ValueError("All Pollinations models failed")

# ══════════════════════════════════════════════
# FSM States & Flow
# ══════════════════════════════════════════════
class ImageGenStates(StatesGroup):
    waiting_prompt_or_image = State()
    waiting_ratio = State()
    waiting_format = State()

@router.message(ImageGenStates.waiting_prompt_or_image, F.text | F.photo)
async def process_prompt_or_image(message: Message, state: FSMContext, bot: Bot):
    # Skip standard menus
    menu_buttons = [uz.MENU_BTN_AI_WORKERS, uz.MENU_BTN_FREE_LESSONS, uz.MENU_BTN_CLUB, uz.MENU_BTN_COURSE, uz.MENU_BTN_BACK]
    if message.text and message.text in menu_buttons:
        await state.clear()
        return

    prompt = message.caption if message.photo else message.text
    if not prompt:
        prompt = "Create an amazing image based on this reference."
        
    ref_image_id = None
    if message.photo:
        ref_image_id = message.photo[-1].file_id

    await state.update_data(prompt=prompt, ref_image_id=ref_image_id)
    await state.set_state(ImageGenStates.waiting_ratio)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1:1 (Kvadrat)", callback_data="img_ratio:1:1"),
            InlineKeyboardButton(text="16:9 (Keng)", callback_data="img_ratio:16:9"),
        ],
        [
            InlineKeyboardButton(text="9:16 (Vertikal)", callback_data="img_ratio:9:16"),
        ]
    ])
    await message.answer("📏 <b>Surat hajmini (nisbatini) tanlang:</b>", reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(ImageGenStates.waiting_ratio, F.data.startswith("img_ratio:"))
async def process_ratio(call: CallbackQuery, state: FSMContext):
    ratio = call.data.split(":")[1:] # e.g. ["1", "1"] for "1:1"
    ratio_str = ":".join(ratio)
    await state.update_data(ratio=ratio_str)
    await call.message.edit_text(f"✅ Tanlandi: <b>{ratio_str}</b>\n\nEndi qanday shaklda qabul qilasiz?", parse_mode="HTML")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🖼 Surat (Telegram)", callback_data="img_format:photo"),
            InlineKeyboardButton(text="📄 Fayl (Original sifat)", callback_data="img_format:doc"),
        ]
    ])
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await state.set_state(ImageGenStates.waiting_format)

@router.callback_query(ImageGenStates.waiting_format, F.data.startswith("img_format:"))
async def process_format(call: CallbackQuery, state: FSMContext, bot: Bot):
    fmt = call.data.split(":")[1]
    data = await state.get_data()
    prompt = data.get("prompt", "")
    ratio = data.get("ratio", "1:1")
    ref_image_id = data.get("ref_image_id")
    
    # Spend tokens
    async with async_session() as session:
        if not await spend_tokens_async(session, call.from_user.id, IMAGE_COST):
            tokens = await get_tokens_async(session, call.from_user.id)
            await state.clear()
            await call.message.edit_text(uz.AI_WORKERS_NO_TOKENS.format(needed=IMAGE_COST, have=tokens), parse_mode="HTML")
            return
        await session.commit()

    await call.message.edit_text("🎨 Surat tayyorlanmoqda... ⏳\nBu 10-30 soniya olishi mumkin.", parse_mode="HTML")
    await call.answer()

    # Pre-download image if provided
    ref_image_bytes = None
    if ref_image_id:
        file = await bot.get_file(ref_image_id)
        bio = BytesIO()
        await bot.download_file(file.file_path, bio)
        ref_image_bytes = bio.getvalue()

    try:
        final_prompt = _build_english_prompt(prompt)
        image_data = None
        
        # 1. Gemini (Nano Banana)
        try:
            image_data = await asyncio.to_thread(_generate_gemini_image, final_prompt, ratio, ref_image_bytes)
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")

        # 2. Pollinations
        if not image_data:
            if ref_image_id:
                # Pollinations currently doesn't easily accept our local uploaded bytes without hosting them.
                raise Exception("Image-to-Image reference failed on main API.")
            image_data = await asyncio.to_thread(_generate_pollinations_image, final_prompt, ratio)
            
        if not image_data:
            raise Exception("Timeout / Generatsiya muvaffaqiyatsiz bo'ldi")

        # Success - send
        async with async_session() as session:
            tokens = await get_tokens_async(session, call.from_user.id)
            
        caption = uz.IMAGEGEN_SUCCESS.format(prompt=prompt[:200], tokens=tokens)
        photo_file = BufferedInputFile(image_data, filename="image.jpg")
        
        if fmt == "doc":
            await bot.send_document(chat_id=call.from_user.id, document=photo_file, caption=caption, parse_mode="HTML")
        else:
            await bot.send_photo(chat_id=call.from_user.id, photo=photo_file, caption=caption, parse_mode="HTML")
            
        await call.message.delete()
        await state.clear()
        
    except Exception as e:
        try:
            async with async_session() as session:
                await add_tokens_async(session, call.from_user.id, IMAGE_COST)
                await session.commit()
        except Exception:
            pass
        await state.clear()
        try:
            await call.message.edit_text(f"❌ Xatolik yuz berdi: {str(e)[:200]}\nToken qaytarildi.")
        except Exception:
            pass
