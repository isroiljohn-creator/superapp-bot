"""Speech-to-Text Transcriber AI using faster-whisper."""
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

# Global whisper model cache
_whisper_model = None

def get_whisper_model():
    """Lazy load the Whisper model to save memory."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            # Load small model for efficiency, supports multiple languages including ru and eng.
            # Using cpu with int8 quantization for minimal memory usage.
            _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load whisper model: {e}")
            raise e
    return _whisper_model


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
        
    url = "https://back.aisha.group/api/v2/stt/post/"
    
    # Using 'Api-Key' based on Django REST framework standard for Token/Api-key authentication,
    # or Bearer if it's JWT. Aishai typically uses basic Api-Key or Bearer. Let's try Bearer.
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    # Some older implementations use Authorization: Api-Key xxx
    if '.' in api_key and len(api_key) == 39: 
        # Django API keys often look like XXXXXXXX.YYYYYYYYYYYYYYYYYYYYY
        headers["Authorization"] = f"Api-Key {api_key}"
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(audio_path, 'rb') as f:
                # Need to use form-data
                form = aiohttp.FormData()
                form.add_field('file', f, filename='audio.ogg', content_type='audio/ogg')
                
                async with session.post(url, headers=headers, data=form) as response:
                    res_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            data = json.loads(res_text)
                            return data.get("text", "") or data.get("result", "") or str(data)
                        except json.JSONDecodeError:
                            return res_text
                    elif response.status in [401, 403]:
                        logger.error(f"Aisha API authentication error: {res_text}")
                        return "❌ API Kalit yaroqsiz yoki muddati o'tgan."
                    else:
                        logger.error(f"Aisha API xatosi {response.status}: {res_text}")
                        # Fallback for alternative endpoints if v2/stt/post fails
                        if response.status == 404:
                            pass  # let it fallback
                        return ""
    except Exception as e:
        logger.error(f"Aisha API request error: {e}")
        
    # Standard STT endpoint fallback
    url_v1 = "https://backend.aisha.group/stt"
    try:
        async with aiohttp.ClientSession() as session:
            with open(audio_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('audio', f, filename='audio.ogg', content_type='audio/ogg')
                async with session.post(url_v1, headers=headers, data=form) as response:
                    res_text = await response.text()
                    if response.status == 200:
                        data = json.loads(res_text)
                        return data.get("text", "")
    except Exception:
        pass
        
    return ""
