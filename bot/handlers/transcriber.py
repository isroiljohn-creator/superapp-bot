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
        text = await loop.run_in_executor(None, _transcribe_audio, input_path)
        
        if text:
            # Send text chunks if too long (Telegram limit 4096)
            for i in range(0, len(text), 4000):
                await message.answer(text[i:i+4000])
            await msg.delete()
        else:
            await msg.edit_text("❌ Audiodan matn topilmadi yoki u tushunarsiz.")
            
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


def _transcribe_audio(audio_path: str) -> str:
    """Run faster-whisper to transcribe audio."""
    try:
        model = get_whisper_model()
        segments, info = model.transcribe(audio_path, beam_size=5)
        
        text = ""
        for segment in segments:
            text += segment.text + " "
            
        return text.strip()
    except Exception as e:
        import logging
        logging.getLogger("transcriber").error(f"Whisper processing error: {e}")
        return ""
