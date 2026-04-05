"""Social media downloader — download videos/photos from Instagram, TikTok, YouTube, etc."""
import os
import uuid
import asyncio
import logging
import re

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from bot.fsm.states import MediaDownloadFSM
from bot.locales import uz

router = Router(name="mediadown")
logger = logging.getLogger("mediadown")

# Supported URL patterns
SUPPORTED_PATTERNS = [
    r"(https?://)?(www\.)?(instagram\.com|instagr\.am)/",
    r"(https?://)?(www\.|vm\.|vt\.)?tiktok\.com/",
    r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/",
    r"(https?://)?(www\.)?pinterest\.(com|co\.uk|de|fr)/",
    r"(https?://)?(www\.)?snapchat\.com/",
    r"(https?://)?(www\.)?(twitter\.com|x\.com)/",
    r"(https?://)?(www\.)?facebook\.com/",
    r"(https?://)?(www\.)?reddit\.com/",
    r"(https?://)?(www\.)?linkedin\.com/",
]


def _is_supported_url(text: str) -> bool:
    """Check if the text contains a supported social media URL."""
    for pattern in SUPPORTED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _get_platform_name(url: str) -> str:
    """Get human-readable platform name from URL."""
    platforms = {
        "instagram": "Instagram",
        "instagr.am": "Instagram",
        "tiktok": "TikTok",
        "youtube": "YouTube",
        "youtu.be": "YouTube",
        "pinterest": "Pinterest",
        "snapchat": "Snapchat",
        "twitter": "Twitter/X",
        "x.com": "Twitter/X",
        "facebook": "Facebook",
        "reddit": "Reddit",
        "linkedin": "LinkedIn",
    }
    url_lower = url.lower()
    for key, name in platforms.items():
        if key in url_lower:
            return name
    return "Noma'lum"


@router.message(MediaDownloadFSM.waiting_for_url, F.text)
async def handle_media_url(message: Message, state: FSMContext):
    """Handle URL input for media download."""
    text = message.text.strip()

    # Check for menu/back buttons
    menu_buttons = [
        uz.MENU_BTN_BACK, uz.MENU_BTN_AI_WORKERS, uz.MENU_BTN_FREE_LESSONS,
        uz.MENU_BTN_COURSE, uz.MENU_BTN_PROFILE, uz.MENU_BTN_SUPERAPP,
        uz.SUPERAPP_BTN_VIDEONOTE, uz.SUPERAPP_BTN_MODERATOR,
    ]
    if text in menu_buttons:
        await state.clear()
        return

    # Validate URL
    if not _is_supported_url(text):
        await message.answer(
            "⚠️ Bu havolani tanib ololmadim.\n\n"
            "Qo'llab-quvvatlanadigan platformalar:\n"
            "Instagram, TikTok, YouTube, Pinterest, Snapchat, Twitter/X, Facebook, Reddit, LinkedIn\n\n"
            "To'g'ri havola yuboring yoki chiqish uchun 🔙 Orqaga tugmasini bosing."
        )
        return

    platform = _get_platform_name(text)
    msg = await message.answer(f"⏳ {platform} dan yuklab olinmoqda... Iltimos kuting.\n\n💡 Katta videolar yuklanishi va siqilishi bir necha daqiqa vaqt olishi mumkin.")

    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    output_template = os.path.join(temp_dir, f"{uuid.uuid4()}.%(ext)s")

    try:
        # Use yt-dlp to download (up to 5GB)
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "-o", output_template,
            "--merge-output-format", "mp4",
            "--recode-video", "mp4",
            # Best available quality — if too big, FFmpeg will compress to fit
            "-f", "bestvideo+bestaudio/best",
            "--no-warnings",
            "--no-check-certificates",
            "--socket-timeout", "30",
            "--retries", "3",
            text,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_text = (stderr.decode() + stdout.decode())[:500]
            logger.error(f"yt-dlp error for {text}: {error_text}")

            if "Private" in error_text or "login" in error_text.lower():
                await msg.edit_text(f"🔒 Bu {platform} kontent yopiq (private). Faqat ochiq (public) kontentlarni yuklab olish mumkin.")
            elif "not found" in error_text.lower() or "404" in error_text:
                await msg.edit_text(f"❌ Kontent topilmadi. Havola to'g'riligini tekshiring.")
            elif "Unsupported URL" in error_text:
                await msg.edit_text(f"❌ Bu turdagi havola qo'llab-quvvatlanmaydi.")
            else:
                await msg.edit_text(f"❌ {platform} dan yuklab bo'lmadi.\n\n<pre>{error_text[:300]}</pre>", parse_mode="HTML")
            return

        # Find downloaded file
        downloaded = None
        base_name = output_template.replace(".%(ext)s", "")
        for ext in ["mp4", "mkv", "webm", "mp3", "m4a", "jpg", "jpeg", "png", "webp"]:
            candidate = f"{base_name}.{ext}"
            if os.path.exists(candidate):
                downloaded = candidate
                break

        if not downloaded:
            # Scan temp dir for the file
            uid = os.path.basename(base_name)
            for f in os.listdir(temp_dir):
                if f.startswith(uid):
                    downloaded = os.path.join(temp_dir, f)
                    break

        if not downloaded or not os.path.exists(downloaded):
            await msg.edit_text("❌ Fayl yuklab olindi, lekin topilmadi. Qayta urinib ko'ring.")
            return

        file_size = os.path.getsize(downloaded)

        # If file exceeds Telegram 50MB limit, compress with FFmpeg
        if file_size > 49 * 1024 * 1024:
            size_mb = file_size // (1024*1024)
            try:
                await msg.edit_text(
                    f"🗜 Fayl hajmi <b>{size_mb} MB</b>. Telegram limitiga (50 MB) moslashtirish uchun siqilmoqda...\n\n"
                    f"⏳ Bu jarayon {max(1, size_mb // 50)}-{max(2, size_mb // 25)} daqiqa davom etishi mumkin.",
                    parse_mode="HTML"
                )
            except Exception:
                pass

            try:
                import imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                import shutil
                ffmpeg_exe = shutil.which("ffmpeg")

            if ffmpeg_exe:
                compressed_path = downloaded.rsplit(".", 1)[0] + "_compressed.mp4"

                # Get video duration first
                probe_cmd = [
                    ffmpeg_exe, "-i", downloaded,
                    "-f", "null", "-"
                ]
                probe = await asyncio.create_subprocess_exec(
                    *probe_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                _, probe_err = await probe.communicate()
                
                # Parse duration from stderr
                duration = 60  # default fallback
                probe_text = probe_err.decode()
                import re as re2
                dur_match = re2.search(r"Duration:\s*(\d+):(\d+):(\d+)", probe_text)
                if dur_match:
                    h, m, s = int(dur_match.group(1)), int(dur_match.group(2)), int(dur_match.group(3))
                    duration = max(h * 3600 + m * 60 + s, 1)

                # Target ~45MB to be safe (45 * 8 * 1024 kbit / duration)
                target_bitrate = int((45 * 8 * 1024) / duration)
                audio_bitrate = 96
                video_bitrate = max(target_bitrate - audio_bitrate, 200)

                compress_cmd = [
                    ffmpeg_exe, "-y", "-i", downloaded,
                    "-c:v", "libx264", "-b:v", f"{video_bitrate}k",
                    "-preset", "fast", "-crf", "28",
                    "-c:a", "aac", "-b:a", f"{audio_bitrate}k",
                    "-movflags", "+faststart",
                    compressed_path
                ]
                comp = await asyncio.create_subprocess_exec(
                    *compress_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await comp.communicate()

                if comp.returncode == 0 and os.path.exists(compressed_path):
                    os.remove(downloaded)
                    downloaded = compressed_path
                    file_size = os.path.getsize(downloaded)
            
            # Final check after compression
            if file_size > 50 * 1024 * 1024:
                await msg.edit_text(
                    f"⚠️ Siqishdan keyin ham fayl {file_size // (1024*1024)} MB. "
                    "Iltimos, kichikroq video sinab ko'ring."
                )
                os.remove(downloaded)
                return

        file = FSInputFile(downloaded)
        ext = downloaded.rsplit(".", 1)[-1].lower()

        try:
            await msg.delete()
        except Exception:
            pass

        # Send based on file type
        if ext in ("mp4", "mkv", "webm"):
            await message.answer_video(
                video=file,
                caption=f"📥 {platform} dan yuklandi\n🔗 {text[:60]}",
                supports_streaming=True,
            )
        elif ext in ("mp3", "m4a", "ogg"):
            await message.answer_audio(
                audio=file,
                caption=f"📥 {platform} dan yuklandi",
            )
        elif ext in ("jpg", "jpeg", "png", "webp"):
            await message.answer_photo(
                photo=file,
                caption=f"📥 {platform} dan yuklandi",
            )
        else:
            await message.answer_document(
                document=file,
                caption=f"📥 {platform} dan yuklandi",
            )

    except Exception as e:
        logger.error(f"Media download error: {e}")
        try:
            await msg.edit_text(f"❌ Kutilmagan xatolik: {str(e)[:200]}")
        except Exception:
            pass
    finally:
        # Cleanup
        base_name = output_template.replace(".%(ext)s", "")
        uid = os.path.basename(base_name)
        for f in os.listdir(temp_dir):
            if f.startswith(uid):
                try:
                    os.remove(os.path.join(temp_dir, f))
                except Exception:
                    pass


@router.message(MediaDownloadFSM.waiting_for_url)
async def fallback_media_url(message: Message):
    """Fallback for non-text messages in media download mode."""
    await message.answer(
        "❌ Iltimos, yuklab olmoqchi bo'lgan video/rasm havolasini matn ko'rinishida yuboring.\n\n"
        "Chiqish uchun 🔙 Orqaga tugmasini bosing."
    )
