"""Text-to-Speech Voicer AI using edge-tts."""
import os
import uuid
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.fsm.states import AIVoicerFSM
from bot.locales import uz

router = Router(name="voicer")
logger = logging.getLogger("voicer")


VOICES = {
    "uz-UZ-MadinaNeural": "🇺🇿 O'zbek (Ayol - Madina)",
    "uz-UZ-SardorNeural": "🇺🇿 O'zbek (Erkak - Sardor)",
    "ru-RU-SvetlanaNeural": "🇷🇺 Rus (Ayol - Svetlana)",
    "ru-RU-DmitryNeural": "🇷🇺 Rus (Erkak - Dmitry)",
    "en-US-AriaNeural": "🇺🇸 Ingliz (Ayol - Aria)",
    "en-US-GuyNeural": "🇺🇸 Ingliz (Erkak - Guy)",
}


@router.message(AIVoicerFSM.waiting_for_text, F.text)
async def handle_voicer_text(message: Message, state: FSMContext):
    """Receive text and present voice options."""
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

    # Check text length limits
    if len(text) > 4000:
        await message.answer("⚠️ Ma'lumot juda uzun. Iltimos 4000 belgidan kamroq matn yuboring.")
        return
        
    if len(text) < 2:
        await message.answer("❌ Matn juda qisqa.")
        return

    # Save text to state
    await state.update_data(voice_text=text)

    # Offer voice options
    buttons = []
    for voice_id, label in VOICES.items():
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"tts_voice:{voice_id}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="tts_voice:cancel")])
    
    await message.answer("🔊 Ovoz turini tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.message(AIVoicerFSM.waiting_for_text)
async def fallback_voicer(message: Message):
    await message.answer("❌ Iltimos, faqat matn yuboring. Chiqish uchun '🔙 Orqaga' tugmasini bosing.")


@router.callback_query(AIVoicerFSM.waiting_for_text, F.data.startswith("tts_voice:"))
async def process_voice_selection(callback: CallbackQuery, state: FSMContext):
    """Process selection and generate TTS."""
    voice_idx = callback.data.split(":")[1]
    
    if voice_idx == "cancel":
        await state.clear()
        from bot.keyboards.buttons import superapp_keyboard
        await callback.message.edit_text("❌ Bekor qilindi.")
        await callback.message.answer(uz.SUPERAPP_MENU, parse_mode="HTML", reply_markup=superapp_keyboard())
        return
        
    data = await state.get_data()
    text = data.get("voice_text", "")
    
    if not text:
        await callback.answer("❌ Matn yo'qolgan, qayta yuboring.", show_alert=True)
        return
        
    await state.clear()
    await callback.message.edit_text("⏳ Matn ovozga aylantirilmoqda, iltimos kuting...")
    
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    uid = str(uuid.uuid4())[:8]
    output_path = os.path.join(temp_dir, f"{uid}_voice.mp3")
    
    try:
        # Run edge_tts
        success = await _generate_tts(text, voice_idx, output_path)
        
        if not success or not os.path.exists(output_path):
            await callback.message.edit_text("❌ Ovoz yaratishda xatolik yuz berdi. Balkim matn tarkibida xato belgilar bordir.")
            return
            
        audio_file = FSInputFile(output_path)
        await callback.message.answer_voice(voice=audio_file, caption=f"🗣 {VOICES.get(voice_idx, 'Ovoz')}")
        await callback.message.delete()
        
    except Exception as e:
        logger.error(f"Voicer process error: {e}")
        try:
            await callback.message.edit_text("❌ Tizimda xatolik yuz berdi.")
        except Exception:
            pass
    finally:
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception:
            pass


async def _generate_tts(text: str, voice: str, output_path: str) -> bool:
    """Generate TTS using edge_tts Python API natively."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        import logging
        logging.getLogger("voicer").error(f"edge-tts Python API error: {e}")
        return False
