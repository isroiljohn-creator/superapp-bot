"""
O'zbek tilidagi barcha matnlar (lotin alifbosi).
Markazlashtirilgan lokalizatsiya fayli.
"""

# ──────────────────────────────────────────────
# Registration FSM
# ──────────────────────────────────────────────
WELCOME = (
    "👋 Assalomu alaykum!\n\n"
    "Men sizga AI yordamida pul topish, mijozlar olish va biznesni "
    "avtomatlashtirishda yordam beraman.\n\n"
    "Keling, avval tanishib olaylik!"
)

ASK_NAME = "✍️ Ismingizni kiriting:"

ASK_AGE = "📅 Yoshingizni kiriting:"

ASK_PHONE = (
    "📱 Telefon raqamingizni yuboring.\n"
    "Pastdagi tugmani bosing 👇"
)

SHARE_PHONE_BUTTON = "📱 Raqamni yuborish"

REGISTRATION_COMPLETE = (
    "✅ Ro'yxatdan muvaffaqiyatli o'tdingiz, {name}!\n\n"
    "Endi sizga mos kontent tayyorlayman. "
    "Bir nechta savolga javob bering 👇"
)

INVALID_AGE = "❌ Iltimos, yoshingizni raqam bilan kiriting (masalan: 25)"

INVALID_PHONE = "❌ Iltimos, pastdagi tugmani bosib telefon raqamingizni yuboring."

# ──────────────────────────────────────────────
# Segmentation
# ──────────────────────────────────────────────
ASK_GOAL = "🎯 Asosiy maqsadingiz nima?"

GOAL_MAKE_MONEY = "💰 Pul topish"
GOAL_GET_CLIENTS = "👥 Mijoz olish"
GOAL_AUTOMATE = "⚙️ Biznesni avtomatlashtirish"

ASK_LEVEL = "📊 Hozirgi darajangiz qanday?"

LEVEL_BEGINNER = "🌱 Boshlang'ich"
LEVEL_FREELANCER = "💼 Frilanser"
LEVEL_BUSINESS = "🏢 Biznes egasi"

SEGMENTATION_COMPLETE = (
    "🎉 Ajoyib! Sizga mos kontent tayyorladim.\n\n"
    "Hozir sizga foydali material yuboraman 👇"
)

# ──────────────────────────────────────────────
# Lead magnet
# ──────────────────────────────────────────────
LEAD_MAGNET_INTRO = "🎁 Sizga maxsus material tayyorladim. Marhamat:"

LEAD_MAGNET_OPENED = "✅ Material ochildi! Yaxshilab ko'rib chiqing."

# ──────────────────────────────────────────────
# Smart delay video
# ──────────────────────────────────────────────
DELAYED_VIDEO_TEXT = (
    "🎬 Sizga maxsus klub haqida video tayyorladim.\n"
    "Ko'rib chiqing 👇"
)

LEARN_MORE_BUTTON = "📖 Batafsil ma'lumot"

# ──────────────────────────────────────────────
# Sales funnel
# ──────────────────────────────────────────────
VSL_INTRO = (
    "🚀 {name}, sizga maxsus tayyorlangan video.\n"
    "Bu videoda {level_description} uchun AI bilan "
    "qanday natijalar olish mumkinligini ko'rasiz."
)

BENEFITS_TEXT = (
    "✨ <b>Klub a'zolari uchun imkoniyatlar:</b>\n\n"
    "✅ AI bilan pul topish strategiyalari\n"
    "✅ Shaxsiy mentor yordami\n"
    "✅ Haftalik live darslar\n"
    "✅ Tayyor shablonlar va promptlar\n"
    "✅ Ekskluziv hamjamiyat"
)

CASE_STUDIES_TEXT = (
    "📈 <b>Natijalar:</b>\n\n"
    "👤 Aziz — 3 oyda $2000+/oy\n"
    "👤 Malika — 50+ doimiy mijoz\n"
    "👤 Sardor — biznesni 3x oshirdi\n\n"
    "Siz ham shunday natijaga erisha olasiz! 👇"
)

CTA_SUBSCRIBE = "💎 Klubga a'zo bo'lish"
CTA_SUBSCRIBE_TEXT = (
    "🔥 Hozir klubga qo'shiling!\n\n"
    "💰 Narxi: {price} so'm/oy\n\n"
    "Tugmani bosing 👇"
)

# ──────────────────────────────────────────────
# Subscription
# ──────────────────────────────────────────────
PAYMENT_SUCCESS = (
    "🎉 To'lov muvaffaqiyatli!\n\n"
    "Sizga klub guruhiga qo'shilish havolasi:\n"
    "{invite_link}\n\n"
    "Xush kelibsiz! 🚀"
)

PAYMENT_FAILED = (
    "❌ To'lov amalga oshmadi.\n"
    "Iltimos, qayta urinib ko'ring yoki "
    "yordam uchun /help buyrug'ini yuboring."
)

SUBSCRIPTION_EXPIRED = (
    "⏰ Sizning obunangiz muddati tugadi.\n"
    "Davom etish uchun qayta obuna bo'ling 👇"
)

# ──────────────────────────────────────────────
# Churn prevention
# ──────────────────────────────────────────────
CHURN_DAY_1 = (
    "👋 {name}, obunangiz tugashi yaqin.\n"
    "Klubdagi barcha imkoniyatlardan foydalanyapsizmi?"
)

CHURN_DAY_3 = (
    "🎬 {name}, sizga maxsus video tayyorladim.\n"
    "Klub a'zolari qanday natijalar olayotganini ko'ring 👇"
)

CHURN_DAY_5 = (
    "🎁 {name}, siz uchun maxsus taklif!\n\n"
    "Chegirmali narx: {discounted_price} so'm/oy\n"
    "Bu taklif faqat 48 soat amal qiladi! ⏳"
)

CHURN_DAY_7 = (
    "😔 {name}, afsuski obunangiz yakunlandi.\n"
    "Istalgan vaqt qaytib kelishingiz mumkin!\n\n"
    "Qayta obuna bo'lish 👇"
)

# ──────────────────────────────────────────────
# Referral
# ──────────────────────────────────────────────
REFERRAL_LINK_TEXT = (
    "🔗 Sizning shaxsiy taklif havolangiz:\n\n"
    "<code>{link}</code>\n\n"
    "Do'stlaringizni taklif qiling va mukofot oling! 🎁"
)

REFERRAL_NEW = "🎉 Yangi taklif! {referred_name} sizning havolangiz orqali qo'shildi."

REFERRAL_VALID = (
    "✅ {referred_name} ro'yxatdan o'tdi!\n"
    "Sizning balansingiz: {balance} so'm"
)

REFERRAL_REWARD = (
    "💰 Tabriklaymiz! {referred_name} obuna bo'ldi.\n"
    "Sizga {reward} so'm mukofot berildi!\n"
    "Jami balans: {total_balance} so'm"
)

REFERRAL_FRAUD_WARNING = "⚠️ Shubhali faoliyat aniqlandi. Taklif hisobga olinmadi."

# ──────────────────────────────────────────────
# Smart reminders (payment abandonment)
# ──────────────────────────────────────────────
REMINDER_1H = (
    "👋 {name}, to'lovda muammo bormi?\n"
    "Yordam kerak bo'lsa yozing, biz doim tayyormiz!"
)

REMINDER_24H = (
    "📈 {name}, mana bu natijani ko'ring!\n"
    "Klub a'zosi {case_name} qanday muvaffaqiyatga erishganini o'qing 👇"
)

REMINDER_48H = (
    "🎁 {name}, siz uchun maxsus bonus!\n"
    "Hozir obuna bo'lsangiz — qo'shimcha 7 kun bepul!"
)

REMINDER_72H = (
    "⏰ {name}, bu sizning oxirgi imkoniyatingiz!\n"
    "Maxsus taklif bugun tugaydi.\n\n"
    "Klubga qo'shilish 👇"
)

# ──────────────────────────────────────────────
# Admin
# ──────────────────────────────────────────────
ADMIN_ONLY = "⛔ Bu buyruq faqat adminlar uchun."

BROADCAST_STARTED = "📤 Xabar yuborish boshlandi: {count} ta foydalanuvchiga"
BROADCAST_COMPLETE = "✅ Xabar yuborildi: {sent}/{total}"

STATS_HEADER = (
    "📊 <b>Statistika</b>\n\n"
    "👥 Jami foydalanuvchilar: {total_users}\n"
    "✅ Ro'yxatdan o'tganlar: {registered}\n"
    "💎 Aktiv obunalar: {active_subs}\n"
    "🔗 Jami takliflar: {total_referrals}\n"
    "💰 Jami daromad: {total_revenue} so'm"
)

# ──────────────────────────────────────────────
# Mini course
# ──────────────────────────────────────────────
COURSE_MODULE_LOCKED = "🔒 Bu modul hali ochilmagan. Oldingi modulni tugating."
COURSE_MODULE_COMPLETE = "✅ Modul tugatildi! Keyingisiga o'ting 👇"
COURSE_ALL_COMPLETE = "🎉 Tabriklaymiz! Barcha modullarni tugatdingiz."

# ──────────────────────────────────────────────
# General
# ──────────────────────────────────────────────
ERROR_GENERAL = "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
HELP_TEXT = (
    "ℹ️ <b>Yordam</b>\n\n"
    "/start — Botni ishga tushirish\n"
    "/profile — Profilim\n"
    "/referral — Taklif havolam\n"
    "/help — Yordam\n"
)

PROFILE_TEXT = (
    "👤 <b>Profilingiz</b>\n\n"
    "📛 Ism: {name}\n"
    "📅 Yosh: {age}\n"
    "📱 Telefon: {phone}\n"
    "🎯 Maqsad: {goal}\n"
    "📊 Daraja: {level}\n"
    "💎 Obuna: {subscription}\n"
    "⭐ Ball: {score}\n"
    "🔗 Takliflar: {referrals}"
)

LEVEL_DESCRIPTIONS = {
    "beginner": "boshlang'ichlar",
    "freelancer": "frilanserlar",
    "business": "biznes egalari",
}
