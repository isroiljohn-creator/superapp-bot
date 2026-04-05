"""Handler to transform user videos into Telegram Video Notes (circular videos)."""
import os
import uuid
import asyncio
import shutil
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from bot.fsm.states import VideoNoteFSM

router = Router(name="videonote")

@router.message(VideoNoteFSM.waiting_for_video, F.video | F.document)
async def process_video_to_note(message: Message, state: FSMContext):
    # Check if it's a valid video format
    if message.document and (not message.document.mime_type or not message.document.mime_type.startswith("video/")):
        await message.answer("❌ Iltimos, faqat video fayl yuboring!")
        return
        
    await state.clear()
        
    # Only react in private chats
    if message.chat.type != "private":
        return
    
    file_obj = message.video or message.document
    
    # Telegram Cloud bot API limit is 20MB for downloads
    if file_obj.file_size and file_obj.file_size > 20 * 1024 * 1024:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
        from bot.config import settings

        base_url = settings.WEBAPP_URL or f"https://{settings.RAILWAY_PUBLIC_DOMAIN}"
        app_url = f"{base_url.rstrip('/')}/tools/videonote.html"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🎥 Mini ilovada yuklash",
                web_app=WebAppInfo(url=app_url),
            )]
        ])
        await message.answer(
            "⚠️ Bu video hajmi <b>20 MB</b> dan katta ekan.\n"
            "Telegram botlari chatda faqat 20 MB gacha fayllarni yuklay oladi.\n\n"
            "Lekin tashvishlanmang! Quyidagi tugmani bosib, <b>Mini ilova</b> orqali "
            "katta videoni ham dumaloq qilib olishingiz mumkin! 👇",
            parse_mode="HTML",
            reply_markup=kb,
        )
        return
    
    # Send processing message
    msg = await message.answer("🔄 Videongiz dumaloq qilib tayyorlanmoqda... Iltimos kuting (1-2 daqiqa vaqt olishi mumkin).")
    # Using local temp folder to avoid /tmp permission issues
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    input_path = os.path.join(temp_dir, f"{uuid.uuid4()}.mp4")
    output_path = os.path.join(temp_dir, f"{uuid.uuid4()}_note.mp4")
    
    try:
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            import shutil
            ffmpeg_exe = shutil.which("ffmpeg")
            
        if not ffmpeg_exe:
            raise RuntimeError("ffmpeg dasturi serverda o'rnatilmagan (yoki topilmadi).")
            
        # Download the file from Telegram
        await message.bot.download(file_obj, destination=input_path)
        
        # FFmpeg command to crop exactly 1:1, max 640x640, duration max 60s
        # Telegram expects video notes to be square and max 1 minute length
        cmd = [
            ffmpeg_exe, "-y", "-i", input_path,
            "-t", "60", # enforce 60s max length
            "-vf", "crop='min(iw,ih)':'min(iw,ih)',scale=640:640",
            "-c:v", "libx264", "-crf", "26", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "128k",
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        if process.returncode != 0:
            await msg.edit_text("❌ Videoni qayta ishlashda xatolik yuz berdi. Iltimos, boshqa fayl yuborib ko'ring (yoki hajmi juda katta bo'lishi mumkin).")
            return

        # Send the file back to the user
        video_note = FSInputFile(output_path)
        await message.answer_video_note(video_note)
        await msg.delete()
        
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        if "VOICE_MESSAGES_FORBIDDEN" in str(e):
            tutorial_text = (
                "❌ <b>Yuborib bo'lmadi!</b>\n\n"
                "Sizning Telegram akkauntingizda botlardan <b>Ovozli va Video xabarlar</b> qabul qilish bloklangan ekan.\n\n"
                "⚙️ <b>Buni qanday to'g'rilash mumkin?</b>\n"
                "1. Telegram sozlamalariga (Settings) kiring.\n"
                "2. Maxfiylik va Xavfsizlik (Privacy and Security) bo'limini tanlang.\n"
                "3. <b>Voice Messages</b> (Ovozli xabarlar) qatorini bosing.\n"
                "4. Pastdagi <i>Always Allow</i> (Doim ruxsat beriladiganlar) ro'yxatiga ushbu botni qo'shing yoki 'Everyone' ni belgilang.\n\n"
                "Shundan so'ng bot bemalol sizga dumaloq video yubora oladi!"
            )
            await msg.edit_text(tutorial_text, parse_mode="HTML")
        else:
            await msg.edit_text(f"❌ Kutilmagan server xatoligi yuz berdi:\n<pre>{str(e)[:500]}</pre>", parse_mode="HTML")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


@router.message(VideoNoteFSM.waiting_for_video)
async def fallback_videonote(message: Message):
    await message.answer("❌ Iltimos, kutilgan forma bo'yicha video fayl yuboring. Chiqish uchun Asosiy menyu yoki '🔙 Orqaga' tugmasini bosing.")
