"""Smart File Compressor AI."""
import os
import uuid
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from bot.fsm.states import AICompressorFSM
from bot.locales import uz

router = Router(name="compressor")
logger = logging.getLogger("compressor")


@router.message(AICompressorFSM.waiting_for_file, F.text)
async def handle_compressor_text(message: Message, state: FSMContext):
    """Handle text commands for compressor."""
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

    await message.answer("❌ Iltimos, fayl yuboring yoki '🔙 Orqaga' tugmasini bosing.")


@router.message(AICompressorFSM.waiting_for_file, F.video | F.photo | F.document)
async def process_compression(message: Message, state: FSMContext):
    """Compress the received media or document."""
    file_id = None
    file_type = None
    original_name = None
    
    if message.video:
        file_id = message.video.file_id
        file_type = "video"
        original_name = message.video.file_name or "video.mp4"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
        original_name = "photo.jpg"
    elif message.document:
        mime = message.document.mime_type
        if mime:
            if mime.startswith("video/"):
                file_type = "video"
            elif mime.startswith("image/"):
                file_type = "photo"
            elif mime == "application/pdf":
                file_type = "pdf"
        
        if not file_type:
            await message.answer("❌ Men faqat Video, Rasm va PDF fayllarni siqa olaman.")
            return
            
        file_id = message.document.file_id
        original_name = message.document.file_name or f"file.{file_type}"
    else:
        await message.answer("❌ Qo'llab-quvvatlanmaydigan fayl turi.")
        return

    await state.clear()
    msg = await message.answer("⏳ Fayl yuklanib siqish jarayoni boshlanmoqda, iltimos kuting...")
    
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    uid = str(uuid.uuid4())[:8]
    ext = original_name.split('.')[-1] if '.' in original_name else file_type
    
    input_path = os.path.join(temp_dir, f"{uid}_in.{ext}")
    output_path = os.path.join(temp_dir, f"{uid}_out_compressed.{ext}")
    
    try:
        await message.bot.download(file_id, destination=input_path)
        original_size = os.path.getsize(input_path)
        
        await msg.edit_text(f"🗜 Asl hajm: **{original_size / (1024*1024):.1f} MB**.\nSiqilmoqda...")
        
        loop = asyncio.get_running_loop()
        success = False
        
        if file_type == "video":
            success = await loop.run_in_executor(None, _compress_video, input_path, output_path)
        elif file_type == "photo":
            success = await loop.run_in_executor(None, _compress_photo, input_path, output_path)
        elif file_type == "pdf":
            success = await loop.run_in_executor(None, _compress_pdf, input_path, output_path)
            
        if not success or not os.path.exists(output_path):
            await msg.edit_text("❌ Siqish jarayonida xatolik yuz berdi yoki bu faylni buning imkoni yo'q.")
            return
            
        new_size = os.path.getsize(output_path)
        saved_mb = (original_size - new_size) / (1024*1024)
        percent = 100 - (new_size / original_size * 100) if original_size > 0 else 0
        
        if new_size >= original_size:
            await msg.edit_text("⚠️ Bu faylni bundan ortiq siqib bo'lmas ekan.")
            return
            
        result_file = FSInputFile(output_path, filename=f"compressed_{original_name}")
        caption = f"✅ <b>Siqish yakunlandi!</b>\n\n🔻 Asl hajm: {original_size/(1024*1024):.2f} MB\n📉 Yangi hajm: {new_size/(1024*1024):.2f} MB\n"
        caption += f"🎉 <b>Foyda:</b> {saved_mb:.2f} MB ({percent:.1f}%)"
        
        if file_type == "video":
            await message.answer_video(video=result_file, caption=caption, parse_mode="HTML")
        else:
            await message.answer_document(document=result_file, caption=caption, parse_mode="HTML")
            
        await msg.delete()
        
    except Exception as e:
        logger.error(f"Compressor process error: {e}")
        try:
            await msg.edit_text("❌ Tizimda xatolik yuz berdi.")
        except Exception:
            pass
    finally:
        for p in [input_path, output_path]:
            try:
                if os.path.exists(p): os.remove(p)
            except Exception: pass


def _compress_video(input_path: str, output_path: str) -> bool:
    """Compress video using FFmpeg."""
    try:
        import subprocess
        import shutil
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            try:
                import imageio_ffmpeg
                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                return False
                
        # Compress using H.264 with high CRF (Constant Rate Factor) to heavily reduce size
        cmd = [
            ffmpeg, "-y", "-i", input_path,
            "-vcodec", "libx264", "-crf", "30", "-preset", "fast",
            "-acodec", "aac", "-b:a", "96k",
            output_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        import logging
        logging.getLogger("compressor").error(f"Video compress error: {e}")
        return False

def _compress_photo(input_path: str, output_path: str) -> bool:
    """Compress image using Pillow."""
    try:
        from PIL import Image
        img = Image.open(input_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Resize if huge, and save with lower quality
        img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
        img.save(output_path, "JPEG", optimize=True, quality=65)
        return True
    except Exception as e:
        import logging
        logging.getLogger("compressor").error(f"Image compress error: {e}")
        return False

def _compress_pdf(input_path: str, output_path: str) -> bool:
    """Compress PDF by removing embedded content using PyPDF2."""
    try:
        from PyPDF2 import PdfReader, PdfWriter
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            # We compress page contents
            page.compress_content_streams()
            writer.add_page(page)
            
        with open(output_path, "wb") as f:
            writer.write(f)
        return True
    except Exception as e:
        import logging
        logging.getLogger("compressor").error(f"PDF compress error: {e}")
        return False
