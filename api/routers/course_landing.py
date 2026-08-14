"""NUVI AI 2.0 — standalone course sales page (nuvi.uz/kurs).

Public endpoints: serve the editable content tree, accept a "manager will
call you back" lead, and record anonymous funnel events. All copy lives in
the DB (CourseLandingContent) so the admin panel can edit every text/image
block without a deploy; DEFAULT_CONTENT below is only the seed used the
first time the page is requested.
"""
import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select

from db.database import async_session
from db.models import CourseLandingContent, CourseLandingEvent, CourseLandingLead

router = APIRouter(prefix="/api/course-landing", tags=["course-landing"])

SLUG = "nuvi_ai_2"
TARIFFS = {"standard", "premium", "vip"}
EVENT_TYPES = {
    "page_view", "modules_view", "pricing_view", "lead_form_view", "lead_submitted",
    "cta_click:standard", "cta_click:premium", "cta_click:vip", "cta_click:hero",
}

DEFAULT_CONTENT = {
    "hero": {
        "badge": "Yangi oqim",
        "title": "NUVI AI 2.0",
        "subtitle": "Sun'iy intellekt yordamida 0 dan yangi kasbga chiqing va kamida 1000$ doimiy o'sib boruvchi daromadga ega bo'ling.",
        "cta": "Ariza qoldirish",
        "meta": ["30+ dars", "6 asosiy + 6 bonus modul", "3+ mehmon spiker"],
        "image": "",
    },
    "audience": {
        "title": "Kurs kimlar uchun?",
        "subtitle": "Agar siz:",
        "items": [
            "O'zingizga mos zamonaviy kasb tanlab, onlayn daromad qilishni xohlasangiz",
            "0 dan yangi kasb orqali kamida 1000$ va doimiy o'sib boruvchi daromadga chiqmoqchi bo'lsangiz",
            "Shaxsiy brendingizni qurib, doimiy yuqori daromad va mijozlar oqimiga erishmoqchi bo'lsangiz",
            "Rasm, video generatsiya va montaj qilib pul ishlashni xohlasangiz",
        ],
    },
    "modules": [
        {
            "badge": "0-Modul", "title": "Foundation",
            "result": "AI orqali daromad qilish xaritasini tushunasiz, o'zingizga mos yo'nalishni tanlaysiz va onlayn to'lovlarni qabul qilishga to'liq tayyor bo'lasiz.",
            "lessons": [
                "AI orqali qaysi kasblarda pul topish mumkin?",
                "Pozitsiyalash (Big Five testi)",
                "Biz uchun eng kerakli ilovalar",
                "Elektron pochta ochish va undan to'g'ri foydalanish",
                "To'lov saytlari va to'lov usullari",
            ], "image": "",
        },
        {
            "badge": "1-Modul", "title": "Prompt engineering",
            "result": "To'g'ri prompt arxitekturasini o'zlashtirasiz, Instagram sahifangizni ochib qadoqlaysiz va birinchi sotuvchi kontentingizni chiqarasiz.",
            "lessons": [
                "Tezkor kirish: ustoz va kurs haqida",
                "O'quv jarayoni: qoidalar va challenge",
                "ChatGPT dagi 8 ta asosiy funksiya",
                "To'g'ri prompt arxitekturasi",
                "Instagram sahifa ochish va qadoqlash",
                "Instagram uchun sotuvchi kontent tayyorlash",
            ], "image": "",
        },
        {
            "badge": "2-Modul", "title": "AI orqali professional rasmlar",
            "result": "Karusel, banner, infografika va neyro-fotosessiya tayyorlashni o'rganasiz — birinchi buyurtmalarni mustaqil bajara olasiz.",
            "lessons": [
                "Kirish darsi", "AI orqali karusel postlar | 1-qism", "AI orqali karusel postlar | 2-qism",
                "2 qadamda prezentatsiya tayyorlash", "AI orqali YouTube bannerlar", "Professional neyro fotosessiya",
                "AI influencer modellarini tayyorlash", "Multfilmlar uchun kadrlar tayyorlash", "Marketplace uchun infografik post",
            ], "image": "",
        },
        {
            "badge": "3-Modul", "title": "AI orqali professional videolar",
            "result": "Realistik videolar, animatsiya, musiqa va kliplar yaratasiz — video xizmatlarini mijozlarga sotishni boshlaysiz.",
            "lessons": [
                "Realistik videolar generatsiya qilish", "Personajlarni animatsiya qilish", "Google Flow dan to'g'ri foydalanish",
                "Videoroliklar uchun realistik rasmlar", "AI orqali musiqa tayyorlash", "Kling AI bilan tanishuv",
                "AI modellar orqali blog yuritish", "Kino va minifilmlar tayyorlash", "Musiqa uchun kliplar tayyorlash",
                "Trenddagi \"uchadigan\" videolar",
            ], "image": "",
        },
        {
            "badge": "4-Modul", "title": "Chatbot va AI agent tayyorlash",
            "result": "Instagram va Telegram uchun chatbot hamda AI agent qurasiz va avtomatlashtirish xizmatini sotishni boshlaysiz.",
            "lessons": [
                "ChatPlace'da ro'yxatdan o'tish va chatbot", "Lidmagnit nima va qanday tayyorlanadi?",
                "Lidmagnitni AI lar bilan svyazka qilish", "Instagram uchun AI agent o'rnatish",
                "Instagramni avtomatlashtirish", "Telegram xabarlariga AI agent", "Telegram botlar tayyorlash",
            ], "image": "",
        },
        {
            "badge": "5-Modul", "title": "Mijoz topish va sotuv sirlari",
            "result": "Mijoz topish tizimini qurasiz, sotuv qadamlarini o'zlashtirasiz va xizmatingizni ikki qadamli texnika bilan qimmat sotasiz.",
            "lessons": [
                "Mijoz topish yo'llari", "Sotuv qadamlari", "Narx strategiyasi",
                "Ikki qadamli qimmat sotish | 1-qism", "Ikki qadamli qimmat sotish | 2-qism", "Ikki qadamli qimmat sotish | 3-qism",
            ], "image": "",
        },
    ],
    "bonus_title": "Bundan tashqari siz 6 ta BONUS modulni olasiz",
    "bonus_modules": [
        {
            "badge": "Bonus 1", "title": "Vibecoding",
            "result": "Kod yozishni bilmasangiz ham AI yordamida sayt, telegram bot va biznes platformalarini yig'ishni o'rganasiz.",
            "lessons": [
                "VIBE coding o'zi nima?", "Qaysi kod yozuvchi ilovalar yaxshi?", "VIBE coding bilan sayt yasash",
                "VIBE coding bilan telegram bot yasash", "Telegram uchun ilova yasash", "Bizneslar uchun platforma yasash",
            ], "image": "",
        },
        {
            "badge": "Bonus 2", "title": "Mobilografiya",
            "result": "Faqat telefon yordamida ekspertlik videolarini suratga olib, professional darajada montaj qilishni o'rganasiz.",
            "lessons": [
                "Telefonda ekspertlik videolar syomkasi", "Telefonda video montaj qilish", "AI orqali subtitr qo'yish",
                "Captions ilovasida montaj", "Story-board orqali video montaj",
            ], "image": "",
        },
        {
            "badge": "Bonus 3", "title": "Mindcard va Notion",
            "result": "Bilim va loyihalaringizni tizimlashtirasiz, Notion'ni AI ga moslab shaxsiy ish maydoningizni qurasiz.",
            "lessons": ["XMind ilovasi texnikalari", "Miro ilovasida ishlash", "Notion ilovasi afzalliklari", "Notion'ni AI ga moslashtirish"],
            "image": "",
        },
        {
            "badge": "Bonus 4", "title": "SMM va Marketing asoslari",
            "result": "Maqsadli auditoriyangizni aniqlab, AI yordamida to'xtovsiz ishlaydigan kontent zavodini qurasiz.",
            "lessons": [
                "Kirish", "AI orqali kontent yozish", "AI orqali kontent zavod qurish", "AI orqali sahifani tahlil qilish",
                "Maqsadli auditoriyani aniqlash", "Analizdan foydalanish", "0 dan sahifa ochish va sozlash",
                "Qachon qaysi platforma yaxshi", "Kontent turlari va vazifasi",
            ], "image": "",
        },
        {
            "badge": "Bonus 5", "title": "Blog orqali monetizatsiya",
            "result": "Blogingizni daromad manbaiga aylantirasiz: sotuvchi matnlar, progrev, lidmagnit va VSL varonkasini quyasiz.",
            "lessons": [
                "Kirish", "Sotuvchi matnlar yozish sirlari", "Blog orqali daromadning 3 usuli",
                "Progrev nima, qanday qilinadi", "Lidmagnitlar tayyorlash", "VSL varonkasidan foydalanish",
            ], "image": "",
        },
        {
            "badge": "Bonus 6", "title": "Shaxsiy brend qurish sirlari",
            "result": "Profilingiz DNK sini shakllantirib, shaxsiy brendingiz orqali doimiy mijozlar oqimi va monetizatsiyaga chiqasiz.",
            "lessons": ["Shaxsiy brend asoslari", "Profil DNK si", "Shaxsiy brenddagi xatolar", "Shaxsiy brend orqali monetizatsiya"],
            "image": "",
        },
    ],
    "outcomes": {
        "title": "Natijada nimalarni o'rganasiz",
        "items": [
            "O'zingizga mos zamonaviy kasbni tanlaysiz",
            "AI bilan professional rasm va dizayn yasaysiz",
            "AI bilan realistik videolar generatsiya qilasiz",
            "Chatbot va AI agentlar qurasiz",
            "Mijoz topib, xizmatingizni qimmat sotasiz",
            "Kamida 1000$ oylik daromadga chiqasiz",
        ],
    },
    "extras": {
        "title": "Kurs ichida yana nima bor?",
        "items": [
            {"title": "Jonli efirlar", "desc": "Shaxsan ustoz bilan savol-javob va razborlar"},
            {"title": "3+ TOP mehmon spiker", "desc": "Sohaning kuchli ekspertlaridan alohida darslar"},
            {"title": "Maxsus o'quv platformasi", "desc": "Barcha darslar bir joyda, istalgan vaqtda"},
            {"title": "Tayyor shablonlar", "desc": "Qo'llanma materiallar va AI promptlar bazasi"},
            {"title": "Kuratorlar nazorati", "desc": "Uy vazifalari tekshiriladi va feedback beriladi"},
            {"title": "Sertifikat va ball tizimi", "desc": "Natijangiz baholanadi, kurs oxirida sertifikat"},
        ],
        "footer": "Nazariya + amaliyot + nazorat + sotuv. Siz faqat dars ko'rib, vazifani bajarasiz — qolganini tizim hal qiladi.",
    },
    "pricing": {
        "title": "Kursda asosiy 3 ta tarif bor",
        "tiers": [
            {
                "key": "standard", "name": "STANDARD", "subtitle": "Kursning barcha asosiy modullari",
                "price": "3 497 000", "highlight": False,
                "features": [
                    "5 ta asosiy modulda qatnashish", "Umumiy savol-javob guruhiga qo'shilish",
                    "Uyga vazifa & amaliy topshiriqlar", "3 ta TOP mehmon ekspertlardan darslar",
                    "Maxsus platformada darslar",
                ],
            },
            {
                "key": "premium", "name": "PREMIUM", "subtitle": "Barcha modullar + kuratorlar nazorati",
                "price": "3 997 000", "highlight": True,
                "features": [
                    "Standard tarifidagi hamma narsa", "Tayyor qo'llanma materiallar", "Baholash ball tizimi",
                    "Shaxsan ustoz bilan 4 ta jonli efir", "Kuratorlar bilan 8 ta jonli efir",
                    "Guruhlarda kuratorlar nazorati", "Kichik 30 kishilik guruhlarga ajratish",
                    "30+ qo'shimcha AI promptlar", "Kurs tugagani haqida sertifikat", "Darsliklar 1 oy saqlanib qolinadi",
                ],
            },
            {
                "key": "vip", "name": "VIP", "subtitle": "Shaxsan ustoz nazorati va 1:1 razborlar",
                "price": "8 997 000", "highlight": False,
                "features": [
                    "Premium tarifidagi hamma narsa", "Shaxsan ustoz bilan 8 ta jonli efir",
                    "Guruhlarda shaxsan ustoz nazorati", "Kichik VIP 10 kishilik guruhlar",
                    "50+ qo'shimcha AI promptlar", "Kurs davomida 2 ta 1:1 zoom razbor",
                    "Ustoz sizning sotuvlaringizda yordam beradi", "Ustoz loyihangizda strateg bo'lib qatnashadi",
                    "Eng yaxshi 2 o'quvchi real loyiha bilan ta'minlanadi", "Kursdan so'ng 2 oy shaxsiy nazorat",
                    "Darsliklar 3 oy saqlanib qolinadi", "\"AI Hub\" klubiga bepul qo'shilish",
                ],
            },
        ],
    },
    "faq": [
        {"q": "Kurs qanday formatda o'tadi?", "a": "To'liq onlayn: nazariy + amaliy darslar, jonli efirlar va maxsus platformada istalgan vaqtda ko'rish mumkin bo'lgan video darslar."},
        {"q": "Oldindan tajriba kerakmi?", "a": "Yo'q. Kurs 0-modul (Foundation) bilan boshlanadi va hech qanday oldingi bilim talab qilinmaydi."},
        {"q": "To'lovni qanday amalga oshiraman?", "a": "Ariza qoldiring — menejerimiz siz bilan bog'lanib, tarif va to'lov bo'yicha barcha savollaringizga javob beradi."},
    ],
    "lead_form": {
        "title": "Ariza qoldiring",
        "subtitle": "Ma'lumotlaringizni qoldiring — menejerimiz tez orada siz bilan bog'lanib, barcha savollaringizga javob beradi.",
        "success": "Rahmat! Arizangiz qabul qilindi — tez orada menejerimiz siz bilan bog'lanadi.",
    },
    "footer": {"text": "NUVI AI 2.0 © 2026"},
}


def _default_row_data() -> dict:
    import copy
    return copy.deepcopy(DEFAULT_CONTENT)


class LeadSubmitRequest(BaseModel):
    name: str
    phone: str
    tariff: Optional[str] = None
    session_id: Optional[str] = None
    utm_source: Optional[str] = ""
    utm_campaign: Optional[str] = ""

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 2:
            raise ValueError("Name too short")
        return v[:255]

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v or "")
        if len(digits) < 9:
            raise ValueError("Invalid phone number")
        return (v or "").strip()[:30]

    @field_validator("tariff")
    @classmethod
    def _validate_tariff(cls, v):
        if v and v not in TARIFFS:
            return None
        return v


class EventRequest(BaseModel):
    session_id: str
    event_type: str
    utm_source: Optional[str] = ""
    utm_campaign: Optional[str] = ""


@router.get("/content")
async def get_content():
    """Public: current editable content tree, seeding defaults on first call."""
    async with async_session() as session:
        res = await session.execute(select(CourseLandingContent).where(CourseLandingContent.slug == SLUG))
        row = res.scalar_one_or_none()
        if not row:
            row = CourseLandingContent(slug=SLUG, data=_default_row_data())
            session.add(row)
            await session.commit()
        return row.data


@router.post("/event")
async def track_event(payload: EventRequest):
    """Fire-and-forget funnel beacon — never raises on bad input."""
    if payload.event_type not in EVENT_TYPES or not payload.session_id:
        return {"ok": True}
    async with async_session() as session:
        session.add(CourseLandingEvent(
            session_id=payload.session_id[:64],
            event_type=payload.event_type,
            utm_source=(payload.utm_source or None),
            utm_campaign=(payload.utm_campaign or None),
        ))
        await session.commit()
    return {"ok": True}


@router.post("/lead")
async def submit_lead(payload: LeadSubmitRequest):
    async with async_session() as session:
        lead = CourseLandingLead(
            name=payload.name,
            phone=payload.phone,
            tariff=payload.tariff,
            session_id=(payload.session_id or None),
            utm_source=(payload.utm_source or None),
            utm_campaign=(payload.utm_campaign or None),
        )
        session.add(lead)
        if payload.session_id:
            session.add(CourseLandingEvent(
                session_id=payload.session_id[:64],
                event_type="lead_submitted",
                utm_source=(payload.utm_source or None),
                utm_campaign=(payload.utm_campaign or None),
            ))
        await session.commit()
        lead_id = lead.id

    try:
        from aiogram import Bot
        from bot.config import settings
        tariff_label = {"standard": "Standard", "premium": "Premium", "vip": "VIP"}.get(payload.tariff or "", "Tanlanmagan")
        text = (
            f"🎯 <b>Yangi ariza — NUVI AI 2.0</b>\n\n"
            f"👤 Ism: {payload.name}\n"
            f"📞 Tel: {payload.phone}\n"
            f"💳 Tarif: {tariff_label}\n"
            f"🆔 Ariza #{lead_id}"
        )
        bot = Bot(token=settings.BOT_TOKEN)
        try:
            for aid in settings.ADMIN_IDS:
                try:
                    await bot.send_message(chat_id=aid, text=text, parse_mode="HTML")
                except Exception:
                    pass
        finally:
            await bot.session.close()
    except Exception:
        pass

    return {"ok": True, "id": lead_id}
