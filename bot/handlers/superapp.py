"""Superapp menu handler — hub for extra bot features."""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.locales import uz
from bot.keyboards.buttons import superapp_keyboard

router = Router(name="superapp")


@router.message(F.text == uz.MENU_BTN_SUPERAPP)
async def menu_superapp(message: Message, state: FSMContext):
    """Show Superapp menu."""
    await state.clear()
    
    await message.answer(
        uz.SUPERAPP_MENU, 
        parse_mode="HTML", 
        reply_markup=superapp_keyboard()
    )

@router.message(F.text == uz.SUPERAPP_BTN_VIDEONOTE)
async def prompt_videonote(message: Message, state: FSMContext):
    from bot.fsm.states import VideoNoteFSM
    await state.set_state(VideoNoteFSM.waiting_for_video)
    await message.answer(
        "🎥 Iltimos, menga dumaloq qilmoqchi bo'lgan videongizni yuboring.\n\n"
        "Eslatma: Video eng yaxshisi kvadrat shaklga yaqin bo'lishi va asosiy obyekt o'rtada bo'lishi tavsiya qilinadi!\n\n"
        "(Chiqish uchun Asosiy menyu yoki Orqaga tugmasini bosing)"
    )


@router.message(F.text == uz.SUPERAPP_BTN_MEDIADOWN)
async def prompt_mediadown(message: Message, state: FSMContext):
    from bot.fsm.states import MediaDownloadFSM
    await state.set_state(MediaDownloadFSM.waiting_for_url)
    await message.answer(
        "📥 <b>Media yuklab olish</b>\n\n"
        "Quyidagi platformalardan video yoki rasm havolasini yuboring:\n\n"
        "• Instagram (Reels, Post, Story)\n"
        "• TikTok\n"
        "• YouTube / YouTube Shorts\n"
        "• Pinterest\n"
        "• Snapchat\n"
        "• Twitter / X\n"
        "• Facebook\n"
        "• Reddit, LinkedIn va boshqalar\n\n"
        "Havola yuboring va bot sizga eng sifatli formatda yuklaydi! 👇",
        parse_mode="HTML",
    )


@router.message(F.text == uz.SUPERAPP_BTN_CONVERT)
async def prompt_fileconvert(message: Message, state: FSMContext):
    from bot.fsm.states import FileConvertFSM
    await state.set_state(FileConvertFSM.waiting_for_file)
    await message.answer(
        "🔄 <b>Fayl konvertatsiya</b>\n\n"
        "Istalgan faylni boshqa formatga o'giring:\n\n"
        "🖼 <b>Rasm:</b> JPG, PNG, WebP, BMP, GIF, ICO, TIFF, PDF\n"
        "🎵 <b>Audio:</b> MP3, WAV, OGG, M4A, FLAC, AAC\n"
        "🎬 <b>Video:</b> MP4, AVI, MKV, WebM, MOV, GIF, MP3\n"
        "📄 <b>Hujjat:</b> PDF, TXT, HTML\n\n"
        "Faylni yuboring va bot formatlarni ko'rsatadi! 👇",
        parse_mode="HTML",
    )


@router.message(F.text == uz.SUPERAPP_BTN_BG_REMOVER)
async def prompt_bg_remover(message: Message, state: FSMContext):
    from bot.fsm.states import AIRemoveBGFSM
    await state.set_state(AIRemoveBGFSM.waiting_for_photo)
    await message.answer("✂️ <b>Orqafonni o'chirish</b>\n\nIltimos, orqa fonini o'chirib tashlamoqchi bo'lgan rasmingizni yuboring:", parse_mode="HTML")

@router.message(F.text == uz.SUPERAPP_BTN_TRANSCRIBE)
async def prompt_transcribe(message: Message, state: FSMContext):
    from bot.fsm.states import AITranscribeFSM
    await state.set_state(AITranscribeFSM.waiting_for_audio)
    await message.answer("🎙 <b>Ovozdan matnga</b>\n\nAudio yoki ovozli xabar (voice) yuboring. Men uni matnga aylantirib beraman:", parse_mode="HTML")

@router.message(F.text == uz.SUPERAPP_BTN_SCANNER)
async def prompt_scanner(message: Message, state: FSMContext):
    from bot.fsm.states import AIScannerFSM
    await state.set_state(AIScannerFSM.waiting_for_photos)
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ Tayyor, PDF yaratish")], [KeyboardButton(text=uz.MENU_BTN_BACK)]], resize_keyboard=True)
    await message.answer("📄 <b>Hujjat skaneri</b>\n\nSkaner qilmoqchi bo'lgan sahifalaringizni ketma-ket yuboring. Barchasini yuborib bo'lgach, «✅ Tayyor» tugmasini bosing:", parse_mode="HTML", reply_markup=kb)

@router.message(F.text == uz.SUPERAPP_BTN_VOICER)
async def prompt_voicer(message: Message, state: FSMContext):
    from bot.fsm.states import AIVoicerFSM
    await state.set_state(AIVoicerFSM.waiting_for_text)
    await message.answer("🗣 <b>Matndan ovozga</b>\n\nOvozga aylantirmoqchi bo'lgan matningizni yuboring:", parse_mode="HTML")

@router.message(F.text == uz.SUPERAPP_BTN_COMPRESSOR)
async def prompt_compressor(message: Message, state: FSMContext):
    from bot.fsm.states import AICompressorFSM
    await state.set_state(AICompressorFSM.waiting_for_file)
    await message.answer("🗜 <b>Hajmni qisqartirish</b>\n\nHajmini kichraytirmoqchi bo'lgan Video, Rasm yoki PDF faylini yuboring:", parse_mode="HTML")

@router.message(F.text == uz.SUPERAPP_BTN_TEAM)
async def nuvi_team_fallback(message: Message):
    # Bu handler asosan fallback uchun xizmat qiladi, chunki web_app tugmasi 
    # to'g'ridan to'g'ri mini-app ni ochib yuboradi. Agar desktop/old version bo'lsa
    # shu yerga tushadi.
    from bot.config import settings
    from bot.keyboards.buttons import nuvi_team_inline_keyboard
    
    # We ideally would check DB for is_team_member here, but since this is just a fallback,
    # we can allow it for admins.
    if message.from_user.id in settings.ADMIN_IDS:
        base_url = settings.WEBAPP_URL or f"https://{settings.RAILWAY_PUBLIC_DOMAIN}"
        app_url = f"{base_url.rstrip('/')}/nuviteam/?v=5"
        await message.answer("💼 Nuvi Team ilovasini ochish uchun quyidagi tugmani bosing:", reply_markup=nuvi_team_inline_keyboard(app_url))
    else:
        await message.answer("Siz Nuvi jamoasi ro'yxatida yo'qsiz (Muhim qism yopiq).")

@router.callback_query(F.data == "superapp:back")
async def superapp_back(callback: CallbackQuery):
    """Back to superapp message block (closes it or asks to use keyboard)."""
    await callback.message.delete()
    await callback.answer("Yopildi", show_alert=False)
