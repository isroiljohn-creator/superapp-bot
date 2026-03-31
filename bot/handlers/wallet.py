from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.locales import uz
from bot.fsm.states import WalletTopUpFSM
from db.database import async_session
from services.crm import CRMService
from services.payment import PaymentService

router = Router(name="wallet")

@router.message(F.text == uz.MENU_BTN_WALLET)
async def show_wallet(message: Message):
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(message.from_user.id)
        if not user:
            return
            
    balance = float(user.tokens or 0)
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Hisobni to'ldirish", callback_data="wallet_topup")]
    ])
    
    await message.answer(
        f"💳 <b>Mening Hamyonim</b>\n\n"
        f"Joriy balans: <b>{balance:,.0f} so'm</b>\n\n"
        f"Mablag'ingizdan botning istalgan xizmatlarida (Moderator, AI) foydalanishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=markup
    )

@router.callback_query(F.data == "wallet_topup")
async def ask_topup_amount(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Iltimos, hisobingizni qancha summaga to'ldirmoqchi ekanligingizni raqamda yozib yuboring.\n"
        "(Eng kam miqdor: 10,000 so'm)"
    )
    from bot.fsm.states import WalletTopUpFSM # lazy load if needed
    await state.set_state(WalletTopUpFSM.waiting_for_amount)

@router.message(WalletTopUpFSM.waiting_for_amount)
async def process_topup_amount(message: Message, state: FSMContext):
    text = message.text.replace(" ", "").replace(",", "")
    if not text.isdigit():
        await message.answer("❌ Iltimos, faqat raqam kiriting. Masalan: 50000")
        return
        
    amount = int(text)
    if amount < 10000:
        await message.answer("❌ Eng kam to'ldirish miqdori qoidasi: 10,000 so'm.")
        return
        
    await state.clear()
    
    # Generate payment URLs
    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(message.from_user.id)
        if not user:
            return
            
        payment_service = PaymentService(session)
        payment = await payment_service.create_payment(
            user_id=user.id,
            amount=amount,
            provider="mixed", # will create both links
            referral_discount=0
        )
        await session.commit()
        
        click_url = PaymentService.generate_click_url(payment.id, amount)
        payme_url = PaymentService.generate_payme_url(payment.id, amount)
        
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 Click orqali to'lash", url=click_url)],
        [InlineKeyboardButton(text="🔹 Payme orqali to'lash", url=payme_url)]
    ])
    
    await message.answer(
        f"💳 <b>{amount:,.0f} so'm</b> to'lash uchun quyidagi tizimlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=markup
    )
