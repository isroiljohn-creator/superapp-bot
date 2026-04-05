"""Tools API — video note converter endpoint for large files via Mini App."""
import os
import uuid
import asyncio
import logging

from fastapi import APIRouter, UploadFile, File, Header, HTTPException

from api.auth import validate_init_data, get_telegram_id_from_init_data

logger = logging.getLogger("tools_api")

router = APIRouter(prefix="/api/tools", tags=["tools"])

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


@router.post("/videonote")
async def convert_videonote(
    video: UploadFile = File(...),
    authorization: str = Header(default=""),
):
    """Accept a large video, convert to square video note, send back via bot."""
    # Auth: extract telegram_id from initData
    raw = ""
    if authorization:
        if authorization.startswith("tma ") or authorization.startswith("twa "):
            raw = authorization[4:]
        else:
            raw = authorization
        raw = raw.strip()

    if not raw:
        raise HTTPException(status_code=401, detail="Avtorizatsiya talab qilinadi")

    telegram_id = get_telegram_id_from_init_data(raw)
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Noto'g'ri avtorizatsiya")

    # Validate file type
    if not video.content_type or not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Faqat video fayl qabul qilinadi")

    # Read file with size limit
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)

    input_path = os.path.join(temp_dir, f"{uuid.uuid4()}.mp4")
    output_path = os.path.join(temp_dir, f"{uuid.uuid4()}_note.mp4")

    try:
        # Save uploaded file
        total = 0
        with open(input_path, "wb") as f:
            while True:
                chunk = await video.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Video hajmi 100 MB dan oshmasligi kerak"
                    )
                f.write(chunk)

        # Get ffmpeg binary
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            import shutil
            ffmpeg_exe = shutil.which("ffmpeg")

        if not ffmpeg_exe:
            raise HTTPException(
                status_code=500,
                detail="Server xatoligi: ffmpeg topilmadi"
            )

        # Convert to square video note
        cmd = [
            ffmpeg_exe, "-y", "-i", input_path,
            "-t", "60",
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
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"FFmpeg error: {stderr.decode()[:500]}")
            raise HTTPException(
                status_code=500,
                detail="Videoni qayta ishlashda xatolik yuz berdi"
            )

        # Send via bot
        from aiogram.types import FSInputFile
        from api.main import bot as api_bot

        if not api_bot:
            raise HTTPException(
                status_code=500,
                detail="Bot hozircha tayyor emas. Biroz kutib qayta urinib ko'ring"
            )

        video_note_file = FSInputFile(output_path)

        try:
            await api_bot.send_video_note(
                chat_id=telegram_id,
                video_note=video_note_file,
            )
        except Exception as e:
            err_str = str(e)
            if "VOICE_MESSAGES_FORBIDDEN" in err_str:
                raise HTTPException(
                    status_code=403,
                    detail="Telegram sozlamalaringizda botlardan Video Note qabul qilish bloklangan. "
                           "Settings → Privacy → Voice Messages → Everyone yoki Always Allow ga o'zgartiring."
                )
            raise HTTPException(
                status_code=500,
                detail=f"Telegramga yuborishda xatolik: {err_str[:200]}"
            )

        return {"status": "ok", "message": "Dumaloq video yuborildi!"}

    finally:
        # Cleanup temp files
        for p in (input_path, output_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
