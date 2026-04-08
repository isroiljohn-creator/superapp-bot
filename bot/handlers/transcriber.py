"""Speech-to-Text Transcriber AI using Aisha Cloud API."""
import os
import uuid
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.fsm.states import AITranscribeFSM
from bot.locales import uz

router = Router(name="transcriber")
logger = logging.getLogger("transcriber")


@router.message(AITranscribeFSM.waiting_for_audio, F.text)
async def handle_transcribe_text(message: Message, state: FSMContext):
    """Handle text messages (including back button) during transcribe FSM."""
    text = message.text.strip()
    from bot.keyboards.buttons import superapp_keyboard

    if text == uz.MENU_BTN_BACK or text == uz.MENU_BTN_SUPERAPP:
        await state.clear()
        await message.answer(uz.SUPERAPP_MENU, parse_mode="HTML", reply_markup=superapp_keyboard())
        return

    menu_buttons = [uz.MENU_BTN_AI_WORKERS, uz.MENU_BTN_FREE_LESSONS, uz.MENU_BTN_COURSE, uz.MENU_BTN_PROFILE]
    if text in menu_buttons:
        await state.clear()
        return

    await message.answer("❌ Iltimos, audio yuboring yoki chiqish uchun '🔙 Orqaga' tugmasini bosing.")


@router.message(AITranscribeFSM.waiting_for_audio, F.audio | F.voice | F.video | F.document)
async def process_audio_transcription(message: Message, state: FSMContext):
    """Process received audio and convert to text."""
    # Validate
    file_id = None
    if message.voice:
        file_id = message.voice.file_id
    elif message.audio:
        file_id = message.audio.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.document:
        if message.document.mime_type and (message.document.mime_type.startswith("audio/") or message.document.mime_type.startswith("video/")):
            file_id = message.document.file_id

    if not file_id:
        await message.answer("❌ Iltimos, faqat audio yoki video faylni yuboring!")
        return

    msg = await message.answer("⏳ Audio olinmoqda va matnga o'girilmoqda. Bu biroz vaqt olishi mumkin...")
    
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    uid = str(uuid.uuid4())[:8]
    input_path = os.path.join(temp_dir, f"{uid}_audio_in")
    
    try:
        await message.bot.download(file_id, destination=input_path)
        
        await msg.edit_text("🎙 Sun'iy intellekt ovozni tahlil qilmoqda...")
        
        import asyncio
        loop = asyncio.get_running_loop()
        text = await _transcribe_aisha_api(input_path)
        
        if text:
            for i in range(0, len(text), 4000):
                await message.answer(text[i:i+4000])
            await msg.delete()
        else:
            await msg.edit_text("❌ Audiodan ma'lumot topilmadi yoki u tushunarsiz.")
            
    except Exception as e:
        logger.error(f"Transcriber error: {e}")
        try:
            await msg.edit_text("❌ Tizimda xatolik yuz berdi. Iltimos keyinroq qayta urinib ko'ring.")
        except Exception:
            pass
    finally:
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except Exception:
                pass


async def _transcribe_aisha_api(audio_path: str) -> str:
    """Send audio to Aisha API for transcription."""
    from bot.config import settings
    import aiohttp
    import json
    
    api_key = getattr(settings, "AISHA_API_KEY", None)
    if not api_key:
        logger.error("AISHA_API_KEY sozlanmagan!")
        return "❌ Tizim sozlari to'liq emas (API kaliti yo'q)."
    
    # Aisha uses Django REST Framework — Api-Key auth
    headers = {"Authorization": f"Api-Key {api_key}"}
    
    # Try multiple possible endpoints
    endpoints = [
        ("https://back.aisha.group/api/v2/stt/post/", "file"),
        ("https://back.aisha.group/api/v1/stt/post/", "file"),
        ("https://back.aisha.group/api/v2/stt/", "file"),
    ]
    
    for url, field_name in endpoints:
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                with open(audio_path, 'rb') as f:
                    form = aiohttp.FormData()
                    form.add_field(field_name, f, filename='audio.ogg', content_type='audio/ogg')
                    
                    async with session.post(url, headers=headers, data=form) as response:
                        res_text = await response.text()
                        logger.info(f"Aisha API [{url}] status={response.status} body={res_text[:200]}")
                        
                        if response.status == 200:
                            try:
                                data = json.loads(res_text)
                                # Try common response fields
                                text = data.get("text") or data.get("result") or data.get("transcription") or ""
                                if text:
                                    return text
                                # If response is a dict but no known field, return it stringified
                                return str(data)
                            except json.JSONDecodeError:
                                if res_text.strip():
                                    return res_text.strip()
                        elif response.status in [401, 403]:
                            logger.error(f"Aisha API auth error: {res_text[:200]}")
                            return "❌ API kalit yaroqsiz yoki muddati o'tgan."
                        elif response.status == 404:
                            logger.warning(f"Aisha endpoint {url} not found, trying next...")
                            continue
                        else:
                            logger.error(f"Aisha API error {response.status}: {res_text[:200]}")
                            continue
        except aiohttp.ClientError as e:
            logger.error(f"Aisha API network error for {url}: {e}")
            continue
        except Exception as e:
            logger.error(f"Aisha API unexpected error for {url}: {e}")
            continue
        
    return ""
