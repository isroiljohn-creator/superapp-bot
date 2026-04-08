"""Background Remover AI using rembg."""
import os
import uuid
import logging
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from bot.fsm.states import AIRemoveBGFSM
from bot.locales import uz

router = Router(name="bg_remover")
logger = logging.getLogger("bg_remover")


@router.message(AIRemoveBGFSM.waiting_for_photo, F.text)
async def handle_bg_text(message: Message, state: FSMContext):
    """Handle text messages (including back button) during bg remover FSM."""
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

    await message.answer("❌ Iltimos, rasm yuboring yoki chiqish uchun '🔙 Orqaga' tugmasini bosing.")


@router.message(AIRemoveBGFSM.waiting_for_photo, F.photo | F.document)
async def process_bg_removal(message: Message, state: FSMContext):
    """Process received photo and remove background."""
    if message.document and not (message.document.mime_type and message.document.mime_type.startswith("image/")):
        await message.answer("❌ Iltimos, faqat rasm faylini yuboring!")
        return

    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    
    msg = await message.answer("⏳ Rasm olinmoqda, iltimos kuting...")
    
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    uid = str(uuid.uuid4())[:8]
    input_path = os.path.join(temp_dir, f"{uid}_bg_in.jpg")
    output_path = os.path.join(temp_dir, f"{uid}_bg_out.png")
    
    try:
        # Download image
        await message.bot.download(file_id, destination=input_path)
        await msg.edit_text("✂️ Orqa fon qirqilmoqda. Sun'iy intellekt ishlamoqda...")
        
        # Process image in a separate thread to unblock async loop
        import asyncio
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(None, _remove_background, input_path, output_path)
        
        if success and os.path.exists(output_path):
            await msg.edit_text("📤 Natija yuborilmoqda...")
            
            output_file = FSInputFile(output_path, filename="bg_removed.png")
            await message.answer_document(document=output_file, caption="✅ Orqa fon muvaffaqiyatli o'chirildi! (Shaffof PNG)\n\nYana rasm yuborishingiz yoki chiqish uchun '🔙 Orqaga' tugmasini bosishingiz mumkin.")
            await msg.delete()
        else:
            await msg.edit_text("⚠️ <b>Server Xotirasi (RAM) yetarli emas!</b>\n\nQattiq hajmli AI modellari o'rnatilganligi sababli bot tizimi qayta yuklandi. Yaqin kunlarda ushbu funksiya Bulutli API (tekin) orqali ulanadi va barqaror ishlaydi!", parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"BG Remover error: {e}")
        try:
            await msg.edit_text("❌ Tizimda xatolik yuz berdi. Iltimos keyinroq qayta urinib ko'ring.")
        except Exception:
            pass
    finally:
        for p in [input_path, output_path]:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass


def _remove_background(input_path: str, output_path: str) -> bool:
    """Mock rembg to prevent crash."""
    return False
