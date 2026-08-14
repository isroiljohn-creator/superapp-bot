"""HR interview support — Google Sheets export, PDF candidate card, HR group
notification. Ported from the standalone HR interview bot."""
import io
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("hr_interview")

_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.dirname(_DIR)
FONT_PATH = os.path.join(_PROJECT, "assets", "fonts", "Roboto-Regular.ttf")
FONT_BOLD_PATH = os.path.join(_PROJECT, "assets", "fonts", "Roboto-Bold.ttf")

HEADERS = [
    "Sana", "Telegram", "Ism/Familiya", "Aloqa", "Kim o'zi", "Nima qiladi", "Tajriba va yutuq",
    "Kuchli ko'nikmalar", "Xulqiy misol (STAR)", "Chidamlilik", "Xato va o'sish", "Qiziqishlar",
    "Motivatsiya turi", "Daromad yoki o'sish", "Tanlov sababi", "Qadriyatlar", "Ish uslubi",
    "Kelajak/o'sish", "Qiziqish sababi", "Portfolio", "Nomzod savoli",
]

MCCLELLAND_MAP = {
    "Natija va yutuqlar": "Yutuqqa yo'naltirilgan (Achievement)",
    "Jamoa va munosabatlar": "Aloqaga yo'naltirilgan (Affiliation)",
    "Ta'sir va yetakchilik": "Ta'sirga yo'naltirilgan (Power)",
    "Barqarorlik": "Barqarorlikka yo'naltirilgan (Security)",
    "Yuqori daromad": "Daromadga yo'naltirilgan (Financial)",
}

DETAILED_FIELDS = [
    ("Kasbi va hozirgi professional holati:", "kim_ozi"),
    ("Hozirgi asosiy vazifalari:", "nima_qiladi"),
    ("Tajriba va eng katta kasbiy yutug'i:", "tajriba"),
    ("Kuchli ko'nikmalari (Top 3):", "konikmalar"),
    ("Murakkab vaziyat va yechim (STAR xulqiy misol):", "star"),
    ("Stress va bosim ostida ishlash vaqtidagi tajribasi:", "chidamlilik"),
    ("Eng katta xato va o'rganilgan saboq:", "xato_osish"),
    ("Ishdan tashqari qiziqishlar / Ilhom manbalari:", "qiziqishlar"),
    ("Daromad / Rivojlanish tanlovi izohi:", "daromad_izoh"),
    ("Ish joyidagi qadriyatlar:", "qadriyatlar"),
    ("2-3 yildan keyingi maqsadlar:", "kelajak"),
    ("Vakansiyaga qiziqish sababi:", "nega_vakansiya"),
    ("Portfolio havolasi:", "portfolio"),
    ("Kompaniyaga savoli:", "savol"),
]


def mcclelland_label(raw: str) -> str:
    return MCCLELLAND_MAP.get(raw, raw or "—")


def _sanitize_for_sheet(text) -> str:
    """Prevents spreadsheet formula injection (=, +, -, @ prefixes)."""
    if text is None:
        return "—"
    s = str(text)
    stripped = s.lstrip()
    if stripped and stripped[0] in ("=", "+", "-", "@"):
        return f"'{s}"
    return s or "—"


def _save_to_sheets_sync(sheet_id: str, vacancy_title: str, row: list):
    import gspread

    creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not creds_json_str:
        raise RuntimeError("GOOGLE_CREDENTIALS_JSON not configured")
    info = json.loads(creds_json_str)
    gc = gspread.service_account_from_dict(info)
    sh = gc.open_by_key(sheet_id)

    try:
        ws = sh.worksheet(vacancy_title)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(vacancy_title, rows=1000, cols=len(HEADERS))

    values = ws.get_all_values()
    is_empty = not values or not any(any(cell.strip() for cell in r) for r in values)
    if is_empty:
        ws.append_row(HEADERS, value_input_option="USER_ENTERED")
    ws.append_row(row, value_input_option="USER_ENTERED")


async def save_candidate_to_sheets(vacancy_title: str, sana: str, telegram: str, answers: dict, motivation: str) -> bool:
    """Appends the candidate's row to the vacancy's worksheet. Returns success."""
    import asyncio
    sheet_id = os.getenv("SHEET_ID")
    if not sheet_id:
        return False

    row = [
        sana, telegram,
        answers.get("ism_familiya"), answers.get("aloqa"), answers.get("kim_ozi"),
        answers.get("nima_qiladi"), answers.get("tajriba"), answers.get("konikmalar"),
        answers.get("star"), answers.get("chidamlilik"), answers.get("xato_osish"),
        answers.get("qiziqishlar"), motivation, answers.get("daromad_osish"),
        answers.get("daromad_izoh"), answers.get("qadriyatlar"), answers.get("ish_uslubi"),
        answers.get("kelajak"), answers.get("nega_vakansiya"), answers.get("portfolio"),
        answers.get("savol"),
    ]
    row = [_sanitize_for_sheet(v) for v in row]

    try:
        await asyncio.to_thread(_save_to_sheets_sync, sheet_id, vacancy_title, row)
        return True
    except Exception as e:
        logger.error(f"HR Sheets export failed: {e}")
        return False


def generate_candidate_pdf(vacancy_title: str, sana: str, telegram: str, answers: dict, motivation: str) -> bytes:
    """Generates a print-ready PDF profile card for the candidate."""
    from fpdf import FPDF

    class CandidatePDF(FPDF):
        def header(self):
            if self.page_no() == 1:
                self.set_fill_color(26, 115, 232)
                self.rect(0, 0, 210, 25, "F")

        def footer(self):
            self.set_y(-15)
            self.set_font("Roboto", "", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"Sahifa {self.page_no()}/{{nb}}", align="C")

    pdf = CandidatePDF()
    pdf.alias_nb_pages()
    pdf.add_font("Roboto", "", FONT_PATH)
    pdf.add_font("Roboto", "B", FONT_BOLD_PATH)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.set_y(35)
    pdf.set_font("Roboto", "B", 18)
    pdf.set_text_color(26, 115, 232)
    ism = answers.get("ism_familiya") or "Nomzod"
    pdf.cell(0, 10, ism.upper(), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Roboto", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Vakansiya: {vacancy_title}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Sana: {sana}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("Roboto", "B", 12)
    pdf.set_text_color(80, 91, 102)
    pdf.cell(0, 8, "Shaxsiy ma'lumotlar", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(225, 228, 232)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    metadata = [
        ("Telegram:", telegram),
        ("Aloqa raqami:", answers.get("aloqa") or "—"),
        ("Motivatsiya turi:", motivation),
        ("Daromad / Rivojlanish:", answers.get("daromad_osish") or "—"),
        ("Ish uslubi:", answers.get("ish_uslubi") or "—"),
        ("Portfolio:", answers.get("portfolio") or "—"),
    ]
    for label, val in metadata:
        pdf.set_font("Roboto", "B", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(45, 6, label, new_x="RIGHT", new_y="TOP")
        pdf.set_font("Roboto", "", 10)
        pdf.set_text_color(34, 34, 34)
        pdf.multi_cell(145, 6, str(val), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Roboto", "B", 12)
    pdf.set_text_color(80, 91, 102)
    pdf.cell(0, 8, "Batafsil savol-javoblar", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    for title, field in DETAILED_FIELDS:
        ans = answers.get(field) or "—"
        pdf.set_font("Roboto", "B", 10)
        pdf.set_text_color(85, 85, 85)
        pdf.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", "", 10)
        pdf.set_text_color(44, 62, 80)
        pdf.set_draw_color(26, 115, 232)
        pdf.set_line_width(0.8)
        pdf.set_fill_color(248, 249, 250)
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        pdf.multi_cell(0, 5, str(ans), border="L", fill=True)
        pdf.set_left_margin(10)
        pdf.set_right_margin(10)
        pdf.ln(4)

    return bytes(pdf.output())


def _escape_md(text) -> str:
    if not text:
        return "—"
    text = str(text)
    for ch in ["*", "_", "`", "["]:
        text = text.replace(ch, f"\\{ch}")
    return text


async def send_hr_notification(bot, hr_chat_id: int, topic_id, vacancy_title: str, sana: str, telegram: str, answers: dict, motivation: str):
    """Sends a Markdown candidate summary + PDF profile card to the HR group."""
    msg = (
        f"📋 *Yangi Nomzod Javoblari ({_escape_md(vacancy_title)})*\n\n"
        f"👤 *Nomzod:* {_escape_md(answers.get('ism_familiya'))}\n"
        f"📅 *Sana:* {_escape_md(sana)}\n"
        f"✈️ *Telegram:* {_escape_md(telegram)}\n"
        f"📞 *Aloqa:* {_escape_md(answers.get('aloqa'))}\n\n"
        f"💼 *Kasbi/Holati:* {_escape_md(answers.get('kim_ozi'))}\n"
        f"📈 *Tajriba va yutuq:* {_escape_md(answers.get('tajriba'))}\n"
        f"💡 *Kuchli ko'nikmalar:* {_escape_md(answers.get('konikmalar'))}\n"
        f"🎯 *Motivatsiya turi:* {_escape_md(motivation)}\n"
        f"💰 *Daromad/O'sish:* {_escape_md(answers.get('daromad_osish'))}\n"
        f"🤝 *Ish uslubi:* {_escape_md(answers.get('ish_uslubi'))}\n"
        f"🔗 *Portfolio:* {_escape_md(answers.get('portfolio'))}\n"
        f"❓ *Nomzod savoli:* {_escape_md(answers.get('savol'))}\n"
    )
    if len(msg) > 4000:
        msg = msg[:3990] + "..."

    try:
        await bot.send_message(chat_id=hr_chat_id, text=msg, parse_mode="Markdown", message_thread_id=topic_id)
    except Exception as e:
        logger.warning(f"HR notify (markdown) failed: {e}, retrying plain")
        try:
            plain = msg.replace("*", "").replace("\\", "")
            await bot.send_message(chat_id=hr_chat_id, text=plain, message_thread_id=topic_id)
        except Exception as e2:
            logger.error(f"HR notify (plain) also failed: {e2}")

    try:
        pdf_bytes = generate_candidate_pdf(vacancy_title, sana, telegram, answers, motivation)
        from aiogram.types import BufferedInputFile
        safe_ism = re.sub(r'[\\/*?:"<>|]', "", answers.get("ism_familiya") or "Nomzod").replace(" ", "_")
        safe_vac = re.sub(r'[\\/*?:"<>|]', "", vacancy_title).replace(" ", "_")
        pdf_file = BufferedInputFile(pdf_bytes, filename=f"Nomzod_{safe_ism}_{safe_vac}.pdf")
        await bot.send_document(
            chat_id=hr_chat_id, document=pdf_file,
            caption=f"📋 {answers.get('ism_familiya') or 'Nomzod'} uchun to'liq anketa kartochkasi",
            message_thread_id=topic_id,
        )
    except Exception as e:
        logger.error(f"HR PDF send failed: {e}")


def uzbekistan_now_str() -> str:
    uzb_tz = timezone(timedelta(hours=5))
    return datetime.now(uzb_tz).strftime("%Y-%m-%d %H:%M")
