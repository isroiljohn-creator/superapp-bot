"""Document Scanner AI using OpenCV."""
import os
import uuid
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, ContentType
from aiogram.fsm.context import FSMContext
from bot.fsm.states import AIScannerFSM
from bot.locales import uz

router = Router(name="scanner")
logger = logging.getLogger("scanner")

@router.message(AIScannerFSM.waiting_for_photos, F.text)
async def handle_scanner_text(message: Message, state: FSMContext):
    """Handle text commands for scanner."""
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

    if text == "✅ Tayyor, PDF yaratish":
        await process_scanned_pdf(message, state)
        return

    await message.answer("❌ Iltimos, skaner qilinadigan rasmlarni yuboring, so'ng '✅ Tayyor, PDF yaratish' tugmasini bosing.")


@router.message(AIScannerFSM.waiting_for_photos, F.photo | F.document)
async def receive_scanner_photo(message: Message, state: FSMContext):
    """Collect photos for scanning."""
    if message.document and not (message.document.mime_type and message.document.mime_type.startswith("image/")):
        await message.answer("❌ Iltimos, faqat rasm faylini yuboring!")
        return

    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    
    data = await state.get_data()
    photos = data.get("photos", [])
    
    if len(photos) >= 20:
        await message.answer("⚠️ Bitta pdf uchun maksimal 20 ta rasm yuborish mumkin. Endi '✅ Tayyor, PDF yaratish' tugmasini bosing.")
        return
        
    photos.append(file_id)
    await state.update_data(photos=photos)
    
    await message.answer(f"📸 {len(photos)}-rasm qabul qilindi. Yana rasm yuboring yoki '✅ Tayyor, PDF yaratish' ni bosing.")


async def process_scanned_pdf(message: Message, state: FSMContext):
    """Process all collected photos and merge into a single PDF."""
    data = await state.get_data()
    photos = data.get("photos", [])
    
    if not photos:
        await message.answer("❌ Hech qanday rasm qabul qilinmadi!")
        return
        
    from bot.keyboards.buttons import superapp_keyboard
    msg = await message.answer(f"⏳ {len(photos)} ta rasm skaner qilinmoqda va PDF tayyorlanmoqda, iltimos kuting...", reply_markup=superapp_keyboard())
    await state.clear()
    
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    uid = str(uuid.uuid4())[:8]
    
    downloaded_paths = []
    output_pdf_path = os.path.join(temp_dir, f"{uid}_scanned.pdf")
    
    try:
        # 1. Download all photos
        for i, file_id in enumerate(photos):
            photo_path = os.path.join(temp_dir, f"{uid}_photo_{i}.jpg")
            await message.bot.download(file_id, destination=photo_path)
            downloaded_paths.append(photo_path)
            
        # 2. Process in executor
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(None, _create_scanned_pdf, downloaded_paths, output_pdf_path)
        
        if not success or not os.path.exists(output_pdf_path):
            await msg.edit_text("❌ PDF yaratishda xatolik yuz berdi.")
            return
            
        # 3. Send PDF
        pdf_file = FSInputFile(output_pdf_path, filename="Nuvi_Scanner.pdf")
        await message.answer_document(document=pdf_file, caption=f"✅ {len(photos)} ta sahifali PDF tayyor! (Kengaytirilgan skaner formati)")
        await msg.delete()
        
    except Exception as e:
        logger.error(f"Scanner process error: {e}")
        try:
            await msg.edit_text("❌ Tizimda xatolik yuz berdi.")
        except Exception:
            pass
    finally:
        for p in downloaded_paths:
            try:
                if os.path.exists(p): os.remove(p)
            except Exception: pass
        try:
            if os.path.exists(output_pdf_path): os.remove(output_pdf_path)
        except Exception: pass


def _create_scanned_pdf(image_paths: list[str], output_pdf: str) -> bool:
    """Enhance images and compile to PDF using OpenCV and Pillow."""
    try:
        import cv2
        import numpy as np
        from PIL import Image

        processed_images = []
        for path in image_paths:
            # Read image
            img = cv2.imread(path)
            if img is None:
                continue

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding to get the "scanned" look
            # It makes background white and text sharp black
            enhanced = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 15
            )
            
            # Convert back to RGB for PIL PDF support
            enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
            
            # Append array to PIL Images
            processed_images.append(Image.fromarray(enhanced_rgb))

        if not processed_images:
            return False

        # Save all as single PDF
        processed_images[0].save(
            output_pdf, "PDF", resolution=150.0, save_all=True, append_images=processed_images[1:]
        )
        return True
    except Exception as e:
        import logging
        logging.getLogger("scanner").error(f"OpenCV processing error: {e}")
        return False
