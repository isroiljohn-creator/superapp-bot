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
FONT_PATH = os.path.join(_PROJECT, "assets", "fonts", "Inter-Regular.ttf")
FONT_BOLD_PATH = os.path.join(_PROJECT, "assets", "fonts", "Inter-Bold.ttf")

# Apple-style palette
_C_BLACK = (29, 29, 31)        # Apple's near-black text
_C_GRAY = (110, 110, 115)      # secondary text
_C_LIGHT_GRAY = (245, 245, 247)  # Apple's card background gray
_C_DIVIDER = (229, 229, 234)
_C_BLUE = (0, 113, 227)        # Apple blue accent

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
    """Generates an Apple-style (clean, minimal, Inter typeface) candidate profile PDF."""
    from fpdf import FPDF

    LM, RM = 18, 18  # left/right margins — generous, Apple-like whitespace
    PAGE_W = 210

    class CandidatePDF(FPDF):
        def footer(self):
            self.set_y(-15)
            self.set_font("Inter", "", 8)
            self.set_text_color(*_C_GRAY)
            self.cell(0, 10, f"{self.page_no()} / {{nb}}", align="C")

    pdf = CandidatePDF()
    pdf.alias_nb_pages()
    pdf.add_font("Inter", "", FONT_PATH)
    pdf.add_font("Inter", "B", FONT_BOLD_PATH)
    pdf.set_left_margin(LM)
    pdf.set_right_margin(RM)
    pdf.set_top_margin(20)
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()

    content_w = PAGE_W - LM - RM

    # ── Header: name, large + bold, then muted meta line ──
    pdf.set_font("Inter", "B", 26)
    pdf.set_text_color(*_C_BLACK)
    ism = answers.get("ism_familiya") or "Nomzod"
    pdf.cell(0, 12, ism, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Inter", "", 11)
    pdf.set_text_color(*_C_GRAY)
    pdf.cell(0, 6, f"{vacancy_title}  ·  {sana}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # ── Quick facts row: small pill-style chips (Apple-esque tags) ──
    chips = [telegram, answers.get("aloqa") or "—", motivation]
    x = LM
    y = pdf.get_y()
    pdf.set_font("Inter", "", 9)
    for chip in chips:
        chip = str(chip)
        w = pdf.get_string_width(chip) + 8
        pdf.set_xy(x, y)
        pdf.set_fill_color(*_C_LIGHT_GRAY)
        pdf.set_text_color(*_C_BLACK)
        pdf.cell(w, 8, chip, fill=True, align="C", new_x="RIGHT", new_y="TOP")
        x += w + 3
    pdf.set_y(y + 8)
    pdf.ln(10)

    # ── Section: Umumiy ma'lumot (two-column key facts, no borders) ──
    _section_title(pdf, "Umumiy ma'lumot", LM, content_w)
    facts = [
        ("Daromad / Rivojlanish", answers.get("daromad_osish") or "—"),
        ("Ish uslubi", answers.get("ish_uslubi") or "—"),
        ("Portfolio", answers.get("portfolio") or "—"),
    ]
    col_w = content_w / 2
    for i, (label, val) in enumerate(facts):
        col_x = LM + (i % 2) * col_w
        if i % 2 == 0:
            row_y = pdf.get_y()
        pdf.set_xy(col_x, row_y)
        pdf.set_font("Inter", "", 8)
        pdf.set_text_color(*_C_GRAY)
        pdf.cell(col_w - 4, 5, label.upper(), new_x="LEFT", new_y="NEXT")
        pdf.set_xy(col_x, pdf.get_y())
        pdf.set_font("Inter", "", 11)
        pdf.set_text_color(*_C_BLACK)
        pdf.multi_cell(col_w - 4, 6, str(val))
        if i % 2 == 1 or i == len(facts) - 1:
            pdf.ln(3)
    pdf.set_y(max(pdf.get_y(), row_y + 20))
    pdf.ln(8)

    # ── Section: Batafsil javoblar — flat cards, rounded corners, no accent borders ──
    _section_title(pdf, "Batafsil javoblar", LM, content_w)
    for title, field in DETAILED_FIELDS:
        ans = str(answers.get(field) or "—")

        pdf.set_font("Inter", "", 10)
        text_h = pdf.multi_cell(content_w - 12, 5.5, ans, dry_run=True, output="LINES")
        body_h = max(len(text_h), 1) * 5.5
        card_h = body_h + 16

        if pdf.get_y() + card_h > pdf.page_break_trigger:
            pdf.add_page()

        card_y = pdf.get_y()
        pdf.set_fill_color(*_C_LIGHT_GRAY)
        pdf.rect(LM, card_y, content_w, card_h, style="F", round_corners=True, corner_radius=3)

        pdf.set_xy(LM + 6, card_y + 5)
        pdf.set_font("Inter", "B", 9)
        pdf.set_text_color(*_C_GRAY)
        pdf.cell(content_w - 12, 5, title, new_x="LMARGIN", new_y="NEXT")

        pdf.set_xy(LM + 6, card_y + 11)
        pdf.set_font("Inter", "", 10)
        pdf.set_text_color(*_C_BLACK)
        pdf.set_left_margin(LM + 6)
        pdf.multi_cell(content_w - 12, 5.5, ans)
        pdf.set_left_margin(LM)

        pdf.set_y(card_y + card_h + 4)

    return bytes(pdf.output())


def _section_title(pdf, text: str, lm: float, content_w: float):
    pdf.set_font("Inter", "B", 13)
    pdf.set_text_color(*_C_BLACK)
    pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y() + 1
    pdf.set_draw_color(*_C_DIVIDER)
    pdf.set_line_width(0.3)
    pdf.line(lm, y, lm + content_w, y)
    pdf.ln(6)


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
