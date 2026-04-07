"""Universal file converter — convert images, audio, video, and documents between formats."""
import os
import uuid
import asyncio
import logging

from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from bot.fsm.states import FileConvertFSM
from bot.locales import uz

router = Router(name="fileconvert")
logger = logging.getLogger("fileconvert")

# ── Supported conversion targets by category ──
FORMATS = {
    "image": {
        "label": "🖼 Rasm",
        "extensions": ["jpg", "jpeg", "png", "webp", "bmp", "gif", "ico", "tiff"],
        "targets": {
            "jpg":  "JPG",
            "png":  "PNG",
            "webp": "WebP",
            "bmp":  "BMP",
            "gif":  "GIF",
            "ico":  "ICO",
            "tiff": "TIFF",
            "pdf":  "PDF",
        },
    },
    "audio": {
        "label": "🎵 Audio",
        "extensions": ["mp3", "wav", "ogg", "m4a", "flac", "aac", "wma", "opus"],
        "targets": {
            "mp3":  "MP3",
            "wav":  "WAV",
            "ogg":  "OGG",
            "m4a":  "M4A",
            "flac": "FLAC",
            "aac":  "AAC",
        },
    },
    "video": {
        "label": "🎬 Video",
        "extensions": ["mp4", "avi", "mkv", "webm", "mov", "flv", "wmv", "3gp"],
        "targets": {
            "mp4":  "MP4",
            "avi":  "AVI",
            "mkv":  "MKV",
            "webm": "WebM",
            "mov":  "MOV",
            "gif":  "GIF",
            "mp3":  "MP3 (faqat audio)",
        },
    },
    "document": {
        "label": "📄 Hujjat",
        "extensions": ["pdf", "docx", "doc", "txt", "csv", "xlsx", "xls", "pptx", "ppt", "html", "md", "json", "xml"],
        "targets": {
            "pdf":  "PDF",
            "txt":  "TXT",
            "html": "HTML",
        },
    },
}

# Mapping mime types to categories
MIME_CATEGORIES = {
    "image": "image",
    "audio": "audio",
    "video": "video",
}


def _detect_category(mime_type: str, filename: str) -> str | None:
    """Detect file category from mime type or extension."""
    if mime_type:
        for prefix, cat in MIME_CATEGORIES.items():
            if mime_type.startswith(prefix):
                return cat

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    for cat, info in FORMATS.items():
        if ext in info["extensions"]:
            return cat
    return None


def _get_extension(filename: str) -> str:
    """Get file extension."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _format_keyboard(category: str, source_ext: str) -> InlineKeyboardMarkup:
    """Build inline keyboard with available target formats."""
    targets = FORMATS.get(category, {}).get("targets", {})
    buttons = []
    row = []
    for ext, label in targets.items():
        if ext == source_ext:
            continue  # Don't show same format
        row.append(InlineKeyboardButton(text=label, callback_data=f"conv:{ext}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="conv:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Handlers ──

@router.message(FileConvertFSM.waiting_for_file, F.text)
async def handle_convert_text(message: Message, state: FSMContext):
    """Handle text messages (menu/back buttons) during file convert FSM."""
    from bot.keyboards.buttons import superapp_keyboard
    text = message.text.strip()

    if text == uz.MENU_BTN_BACK or text == uz.MENU_BTN_SUPERAPP:
        await state.clear()
        await message.answer(uz.SUPERAPP_MENU, parse_mode="HTML", reply_markup=superapp_keyboard())
        return
    menu_buttons = [uz.MENU_BTN_AI_WORKERS, uz.MENU_BTN_FREE_LESSONS, uz.MENU_BTN_COURSE, uz.MENU_BTN_PROFILE]
    if text in menu_buttons:
        await state.clear()
        return

    await message.answer(
        "❌ Iltimos, konvertatsiya qilmoqchi bo'lgan faylingizni yuboring.\n\n"
        "Chiqish uchun 🔙 Orqaga tugmasini bosing."
    )


@router.message(FileConvertFSM.waiting_for_file, F.document | F.photo | F.video | F.audio | F.voice | F.video_note)
async def handle_convert_file(message: Message, state: FSMContext):
    """Receive file and show available target formats."""
    # Determine file info
    if message.document:
        file_id = message.document.file_id
        filename = message.document.file_name or "file"
        mime = message.document.mime_type or ""
        file_size = message.document.file_size
    elif message.photo:
        file_id = message.photo[-1].file_id
        filename = "photo.jpg"
        mime = "image/jpeg"
        file_size = message.photo[-1].file_size
    elif message.video:
        file_id = message.video.file_id
        filename = message.video.file_name or "video.mp4"
        mime = message.video.mime_type or "video/mp4"
        file_size = message.video.file_size
    elif message.audio:
        file_id = message.audio.file_id
        filename = message.audio.file_name or "audio.mp3"
        mime = message.audio.mime_type or "audio/mpeg"
        file_size = message.audio.file_size
    elif message.voice:
        file_id = message.voice.file_id
        filename = "voice.ogg"
        mime = "audio/ogg"
        file_size = message.voice.file_size
    elif message.video_note:
        file_id = message.video_note.file_id
        filename = "videonote.mp4"
        mime = "video/mp4"
        file_size = message.video_note.file_size
    else:
        await message.answer("❌ Bu turdagi fayl qo'llab-quvvatlanmaydi.")
        return

    # Check size (20MB Telegram download limit)
    if file_size and file_size > 20 * 1024 * 1024:
        await message.answer("⚠️ Fayl hajmi 20 MB dan katta. Iltimos, kichikroq fayl yuboring.")
        return

    source_ext = _get_extension(filename)
    category = _detect_category(mime, filename)

    if not category:
        await message.answer(
            "❓ Bu fayl turini aniqlab bo'lmadi.\n"
            "Qo'llab-quvvatlanadigan formatlar: rasm, audio, video, hujjat."
        )
        return

    cat_label = FORMATS[category]["label"]
    targets = FORMATS[category]["targets"]

    # Filter out same format
    available = {k: v for k, v in targets.items() if k != source_ext}
    if not available:
        await message.answer("❌ Bu formatdan boshqa formatlarga o'girish imkoni yo'q.")
        return

    await state.update_data(file_id=file_id, filename=filename, mime=mime, category=category, source_ext=source_ext)
    await state.set_state(FileConvertFSM.waiting_for_format)

    await message.answer(
        f"📁 Fayl qabul qilindi: <b>{filename}</b>\n"
        f"📂 Turi: {cat_label} ({source_ext.upper()})\n\n"
        f"Qaysi formatga o'girmoqchisiz? 👇",
        parse_mode="HTML",
        reply_markup=_format_keyboard(category, source_ext),
    )


@router.message(FileConvertFSM.waiting_for_file)
async def convert_fallback(message: Message):
    """Fallback for unsupported messages."""
    await message.answer(
        "❌ Iltimos, konvertatsiya qilmoqchi bo'lgan fayl, rasm, video yoki audio yuboring.\n\n"
        "Chiqish uchun 🔙 Orqaga tugmasini bosing."
    )


# ── Format selection callback ──

@router.callback_query(FileConvertFSM.waiting_for_format, F.data == "conv:cancel")
async def cancel_convert(callback: CallbackQuery, state: FSMContext):
    """Cancel conversion."""
    await state.set_state(FileConvertFSM.waiting_for_file)
    await callback.message.edit_text("❌ Bekor qilindi. Yangi fayl yuboring yoki 🔙 Orqaga tugmasini bosing.")
    await callback.answer()


@router.callback_query(FileConvertFSM.waiting_for_format, F.data.startswith("conv:"))
async def process_conversion(callback: CallbackQuery, state: FSMContext):
    """Process the actual file conversion."""
    target_ext = callback.data.split(":")[1]
    data = await state.get_data()
    file_id = data.get("file_id")
    filename = data.get("filename", "file")
    category = data.get("category")
    source_ext = data.get("source_ext")

    await state.set_state(FileConvertFSM.waiting_for_file)

    if not file_id or not category:
        await callback.message.edit_text("❌ Fayl ma'lumotlari topilmadi. Qayta fayl yuboring.")
        await callback.answer()
        return

    target_label = FORMATS.get(category, {}).get("targets", {}).get(target_ext, target_ext.upper())
    await callback.message.edit_text(f"⏳ {source_ext.upper()} → {target_label} konvertatsiya qilinmoqda...")
    await callback.answer()

    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    uid = str(uuid.uuid4())[:8]
    input_path = os.path.join(temp_dir, f"{uid}_input.{source_ext}")
    output_name = f"{os.path.splitext(filename)[0]}.{target_ext}"
    output_path = os.path.join(temp_dir, f"{uid}_output.{target_ext}")

    try:
        # Download file from Telegram
        file = await callback.message.bot.get_file(file_id)
        await callback.message.bot.download_file(file.file_path, input_path)

        success = False

        # ── IMAGE conversion ──
        if category == "image":
            if target_ext == "pdf":
                success = await _image_to_pdf(input_path, output_path)
            else:
                success = await _convert_image(input_path, output_path, target_ext)

        # ── AUDIO conversion ──
        elif category == "audio":
            success = await _convert_ffmpeg(input_path, output_path, target_ext, "audio")

        # ── VIDEO conversion ──
        elif category == "video":
            if target_ext == "gif":
                success = await _video_to_gif(input_path, output_path)
            elif target_ext == "mp3":
                success = await _convert_ffmpeg(input_path, output_path, "mp3", "audio_only")
            else:
                success = await _convert_ffmpeg(input_path, output_path, target_ext, "video")

        # ── DOCUMENT conversion ──
        elif category == "document":
            success = await _convert_document(input_path, output_path, source_ext, target_ext)

        if not success or not os.path.exists(output_path):
            await callback.message.edit_text("❌ Konvertatsiya muvaffaqiyatsiz tugadi. Boshqa format sinab ko'ring.")
            return

        # Send result
        result_file = FSInputFile(output_path, filename=output_name)
        file_size = os.path.getsize(output_path)
        size_str = f"{file_size / (1024*1024):.1f} MB" if file_size > 1024*1024 else f"{file_size / 1024:.1f} KB"

        caption = f"✅ <b>Konvertatsiya tayyor!</b>\n📁 {source_ext.upper()} → {target_ext.upper()}\n💾 Hajmi: {size_str}"

        if target_ext in ("mp4", "avi", "mkv", "webm", "mov"):
            await callback.message.answer_video(video=result_file, caption=caption, parse_mode="HTML")
        elif target_ext in ("mp3", "wav", "ogg", "m4a", "flac", "aac"):
            await callback.message.answer_audio(audio=result_file, caption=caption, parse_mode="HTML")
        elif target_ext in ("jpg", "jpeg", "png", "webp", "bmp") and file_size < 10 * 1024 * 1024:
            await callback.message.answer_photo(photo=result_file, caption=caption, parse_mode="HTML")
        elif target_ext == "gif":
            await callback.message.answer_animation(animation=result_file, caption=caption, parse_mode="HTML")
        else:
            await callback.message.answer_document(document=result_file, caption=caption, parse_mode="HTML")

        try:
            await callback.message.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Conversion error: {e}")
        try:
            await callback.message.edit_text(f"❌ Xatolik: {str(e)[:200]}")
        except Exception:
            pass
    finally:
        for p in [input_path, output_path]:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass


# ── Conversion helpers ──

async def _convert_image(input_path: str, output_path: str, target_ext: str) -> bool:
    """Convert image using Pillow."""
    try:
        from PIL import Image
        img = Image.open(input_path)

        # Handle RGBA for formats that don't support it
        if target_ext in ("jpg", "jpeg", "bmp", "ico") and img.mode in ("RGBA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif target_ext in ("jpg", "jpeg", "bmp") and img.mode != "RGB":
            img = img.convert("RGB")

        save_kwargs = {}
        if target_ext in ("jpg", "jpeg"):
            save_kwargs["quality"] = 95
        elif target_ext == "webp":
            save_kwargs["quality"] = 90
        elif target_ext == "ico":
            img = img.resize((256, 256), Image.LANCZOS)

        img.save(output_path, **save_kwargs)
        return True
    except Exception as e:
        logger.error(f"Image convert error: {e}")
        return False


async def _image_to_pdf(input_path: str, output_path: str) -> bool:
    """Convert image to PDF."""
    try:
        from PIL import Image
        img = Image.open(input_path)
        if img.mode in ("RGBA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.save(output_path, "PDF")
        return True
    except Exception as e:
        logger.error(f"Image to PDF error: {e}")
        return False


async def _get_ffmpeg() -> str | None:
    """Get FFmpeg executable path."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        import shutil
        return shutil.which("ffmpeg")


async def _convert_ffmpeg(input_path: str, output_path: str, target_ext: str, mode: str) -> bool:
    """Convert audio/video using FFmpeg."""
    ffmpeg = await _get_ffmpeg()
    if not ffmpeg:
        logger.error("FFmpeg not found")
        return False

    try:
        if mode == "audio":
            cmd = [ffmpeg, "-y", "-i", input_path, "-vn", "-q:a", "2", output_path]
        elif mode == "audio_only":
            cmd = [ffmpeg, "-y", "-i", input_path, "-vn", "-ab", "192k", output_path]
        else:  # video
            cmd = [
                ffmpeg, "-y", "-i", input_path,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                output_path,
            ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return process.returncode == 0
    except Exception as e:
        logger.error(f"FFmpeg convert error: {e}")
        return False


async def _video_to_gif(input_path: str, output_path: str) -> bool:
    """Convert video to GIF using FFmpeg."""
    ffmpeg = await _get_ffmpeg()
    if not ffmpeg:
        return False

    try:
        # Generate palette for better quality
        palette_path = input_path + "_palette.png"
        palette_cmd = [
            ffmpeg, "-y", "-i", input_path,
            "-vf", "fps=12,scale=480:-1:flags=lanczos,palettegen",
            palette_path,
        ]
        p1 = await asyncio.create_subprocess_exec(
            *palette_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await p1.communicate()

        gif_cmd = [
            ffmpeg, "-y", "-i", input_path, "-i", palette_path,
            "-lavfi", "fps=12,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse",
            "-t", "15",  # Max 15 seconds
            output_path,
        ]
        p2 = await asyncio.create_subprocess_exec(
            *gif_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await p2.communicate()

        try:
            os.remove(palette_path)
        except Exception:
            pass

        return p2.returncode == 0
    except Exception as e:
        logger.error(f"Video to GIF error: {e}")
        return False


async def _convert_document(input_path: str, output_path: str, source_ext: str, target_ext: str) -> bool:
    """Convert documents between formats."""
    try:
        if target_ext == "txt":
            # Extract text from various formats
            content = ""
            if source_ext == "pdf":
                # Try basic PDF text extraction
                try:
                    import subprocess
                    # Use pdftotext if available
                    import shutil
                    if shutil.which("pdftotext"):
                        proc = await asyncio.create_subprocess_exec(
                            "pdftotext", input_path, output_path,
                            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                        )
                        await proc.communicate()
                        return proc.returncode == 0
                except Exception:
                    pass
                # Fallback: read raw
                with open(input_path, "rb") as f:
                    raw = f.read()
                    # Simple text extraction from PDF
                    import re
                    texts = re.findall(rb'\((.*?)\)', raw)
                    content = "\n".join(t.decode("latin-1", errors="ignore") for t in texts[:500])
            elif source_ext in ("html", "xml", "md", "json", "csv"):
                with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            elif source_ext == "docx":
                try:
                    from docx import Document
                    doc = Document(input_path)
                    content = "\n".join(p.text for p in doc.paragraphs)
                except ImportError:
                    try:
                        import python_pptx  # just to check if docx-like libs available
                    except ImportError:
                        pass
                    with open(input_path, "rb") as f:
                        content = f.read().decode("utf-8", errors="ignore")
            else:
                with open(input_path, "rb") as f:
                    content = f.read().decode("utf-8", errors="ignore")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            return bool(content.strip())

        elif target_ext == "html":
            with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            html_content = f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Converted</title></head><body><pre>{content}</pre></body></html>"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return True

        elif target_ext == "pdf" and source_ext == "txt":
            # Text to PDF using basic approach
            try:
                from PIL import Image, ImageDraw, ImageFont
                with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()

                lines = text.split("\n")
                line_height = 16
                margin = 40
                page_w, page_h = 595, 842  # A4

                pages = []
                max_lines = (page_h - 2 * margin) // line_height

                for i in range(0, len(lines), max_lines):
                    page_lines = lines[i:i + max_lines]
                    img = Image.new("RGB", (page_w, page_h), "white")
                    draw = ImageDraw.Draw(img)
                    for j, line in enumerate(page_lines):
                        draw.text((margin, margin + j * line_height), line[:90], fill="black")
                    pages.append(img)

                if pages:
                    pages[0].save(output_path, "PDF", save_all=True, append_images=pages[1:])
                    return True
            except Exception as e:
                logger.error(f"TXT to PDF error: {e}")
            return False

    except Exception as e:
        logger.error(f"Document convert error: {e}")
        return False
