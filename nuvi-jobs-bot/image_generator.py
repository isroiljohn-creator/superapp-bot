from PIL import Image, ImageDraw, ImageFont
import os
import logging

logger = logging.getLogger("jarvis.image_generator")

# Hirely brand palette (from the "Hirely Jobs Poster Shablonlari" designs).
DARK_GREEN = (22, 58, 38)      # #163A26
BRIGHT_GREEN = (140, 245, 110)  # #8CF56E
CARD_BG = (247, 250, 246)       # #F7FAF6
MUTED_GREEN = (169, 182, 167)   # #A9B6A7 - labels/eyebrow text
SUBTITLE_GREEN = (31, 74, 48)   # #1F4A30 - italic subtitle on bright green
DIVIDER = (220, 230, 217)       # #DCE6D9
GOLD = (222, 168, 66)           # VIP accent

FONT_DIR = os.path.dirname(os.path.abspath(__file__))
SORA_PATH = os.path.join(FONT_DIR, "Sora-Variable.ttf")
MANROPE_PATH = os.path.join(FONT_DIR, "Manrope-Variable.ttf")


def _vf(path: str, size: int, weight: int) -> ImageFont.FreeTypeFont:
    """Loads a variable font at a given weight, falling back to the
    default face if the file is missing or isn't a variable font."""
    try:
        font = ImageFont.truetype(path, size)
        font.set_variation_by_axes([weight])
        return font
    except Exception:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()


def _wrap(draw, text, font, max_width, max_lines=2):
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        w = draw.textbbox((0, 0), test, font=font)[2]
        if w <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines[:max_lines]


def _wrap_fit(draw, text, sizes, path, weight, max_width, max_lines=2):
    """Wraps at the largest size (descending) that fits the whole text
    within max_lines, falling back to the smallest size otherwise."""
    word_count = len(text.split())
    chosen_font, chosen_lines = None, None
    for size in sizes:
        font = _vf(path, size, weight)
        lines = _wrap(draw, text, font, max_width, max_lines=max_lines)
        chosen_font, chosen_lines = font, lines
        if sum(len(line.split()) for line in lines) >= word_count:
            break
    return chosen_font, chosen_lines


def _hirely_logo(draw, x, y, size, color):
    """Simplified two-person mark (the design's SVG silhouette, redrawn as
    plain shapes since PIL can't render arbitrary SVG)."""
    r = size * 0.24
    draw.ellipse([x, y, x + r * 2, y + r * 2], fill=color)
    draw.rounded_rectangle([x - r * 0.2, y + r * 2.1, x + r * 2.2, y + size], radius=r, fill=color)


def _star(draw, cx, cy, r, color):
    import math
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
    draw.polygon(pts, fill=color)


def _vip_badge(draw, box, bg, text_color, font):
    # The star is drawn as a polygon — the bundled fonts lack the ★ glyph
    # and render a tofu box instead.
    draw.rounded_rectangle(box, radius=18, fill=bg)
    _star(draw, box[0] + 22, (box[1] + box[3]) // 2, 8, text_color)
    draw.text((box[0] + 38, box[1] + 8), "VIP", fill=text_color, font=font)


def _design_a(position, company, salary, is_vip, channel_display) -> Image.Image:
    """'Ramkali' — framed card centered on a dark green canvas."""
    width, height = 1200, 675
    img = Image.new("RGB", (width, height), DARK_GREEN)
    draw = ImageDraw.Draw(img)

    pad = 22
    card = [pad, pad, width - pad, height - pad]
    draw.rounded_rectangle(card, radius=22, fill=CARD_BG)

    accent = GOLD if is_vip else BRIGHT_GREEN
    cx = width // 2

    # Logo row (centered)
    f_wordmark = _vf(SORA_PATH, 26, 800)
    f_pill = _vf(SORA_PATH, 15, 800)
    logo_text_w = draw.textbbox((0, 0), "HIRELY", font=f_wordmark)[2]
    pill_text = "JOBS"
    pill_pad = 12
    pill_w = draw.textbbox((0, 0), pill_text, font=f_pill)[2] + pill_pad * 2
    mark_size = 34
    total_w = mark_size + 10 + logo_text_w + 10 + pill_w
    lx = cx - total_w // 2
    ly = pad + 44
    _hirely_logo(draw, lx, ly, mark_size, DARK_GREEN)
    draw.text((lx + mark_size + 10, ly + 2), "HIRELY", fill=DARK_GREEN, font=f_wordmark)
    pill_x = lx + mark_size + 10 + logo_text_w + 10
    draw.rounded_rectangle([pill_x, ly + 3, pill_x + pill_w, ly + 3 + 24], radius=8, fill=BRIGHT_GREEN)
    draw.text((pill_x + pill_pad, ly + 6), pill_text, fill=DARK_GREEN, font=f_pill)

    if is_vip:
        f_badge = _vf(SORA_PATH, 16, 800)
        _vip_badge(draw, [width - pad - 120, pad + 20, width - pad - 24, pad + 56], accent, DARK_GREEN, f_badge)

    # Subtitle + eyebrow
    f_sub = _vf(MANROPE_PATH, 15, 500)
    sub_text = "Xayrli uchrashuvlar maskani"
    sub_w = draw.textbbox((0, 0), sub_text, font=f_sub)[2]
    draw.text((cx - sub_w // 2, ly + 46), sub_text, fill=MUTED_GREEN, font=f_sub)

    f_eyebrow = _vf(MANROPE_PATH, 12, 700)
    eyebrow_text = "YANGI VAKANSIYA  ·  TEZKOR ARIZA  ·  ISHONCHLI TAKLIF"
    eb_w = draw.textbbox((0, 0), eyebrow_text, font=f_eyebrow)[2]
    draw.text((cx - eb_w // 2, ly + 78), eyebrow_text, fill=MUTED_GREEN, font=f_eyebrow)

    # Bottom footer + company/salary row are anchored to the card bottom;
    # the big title fills whatever room is left above them.
    footer_y = height - pad - 46
    row_y = footer_y - 70

    f_chip_label = _vf(MANROPE_PATH, 11, 700)
    f_chip_val = _vf(SORA_PATH, 19, 600)
    company_lines = _wrap(draw, company, f_chip_val, 340, max_lines=1)
    f_salary, salary_lines = _wrap_fit(draw, salary, [15], SORA_PATH, 700, 340, max_lines=1)

    title_bottom = row_y - 40
    f_title, title_lines = _wrap_fit(draw, position.upper(), [66, 52, 42], SORA_PATH, 800, card[2] - card[0] - 120, max_lines=2)
    title_h = sum(draw.textbbox((0, 0), l, font=f_title)[3] + 8 for l in title_lines)
    y_title = ly + 118 + max(0, (title_bottom - (ly + 118) - title_h) // 2)
    for line in title_lines:
        lw = draw.textbbox((0, 0), line, font=f_title)[2]
        draw.text((cx - lw // 2, y_title), line, fill=DARK_GREEN, font=f_title)
        y_title += draw.textbbox((0, 0), line, font=f_title)[3] + 8

    # Kompaniya | Maosh row
    col_gap = 22
    comp_w = max(draw.textbbox((0, 0), l, font=f_chip_val)[2] for l in company_lines)
    sal_w = max(draw.textbbox((0, 0), l, font=f_salary)[2] for l in salary_lines) + 28
    row_total_w = comp_w + col_gap * 2 + 1 + sal_w
    row_x = cx - row_total_w // 2

    draw.text((row_x, row_y), "KOMPANIYA", fill=MUTED_GREEN, font=f_chip_label)
    for line in company_lines:
        draw.text((row_x, row_y + 18), line, fill=DARK_GREEN, font=f_chip_val)
    divider_x = row_x + comp_w + col_gap
    draw.line([(divider_x, row_y - 4), (divider_x, row_y + 42)], fill=DIVIDER, width=1)

    sal_x = divider_x + col_gap
    draw.text((sal_x, row_y), "MAOSH", fill=MUTED_GREEN, font=f_chip_label)
    for line in salary_lines:
        chip_box = [sal_x, row_y + 16, sal_x + sal_w, row_y + 16 + f_salary.size + 12]
        draw.rounded_rectangle(chip_box, radius=8, fill=BRIGHT_GREEN)
        draw.text((sal_x + 14, row_y + 21), line, fill=DARK_GREEN, font=f_salary)

    # Footer
    draw.line([(card[0] + 56, footer_y - 16), (card[2] - 56, footer_y - 16)], fill=DIVIDER, width=1)
    f_footer = _vf(MANROPE_PATH, 13, 500)
    draw.text((card[0] + 56, footer_y), f"t.me/{channel_display}", fill=MUTED_GREEN, font=f_footer)
    f_footer_r = _vf(MANROPE_PATH, 13, 600)
    r_text = "Hirely Jobs"
    r_w = draw.textbbox((0, 0), r_text, font=f_footer_r)[2]
    draw.text((card[2] - 56 - r_w, footer_y), r_text, fill=MUTED_GREEN, font=f_footer_r)

    return img


def _design_b(position, company, salary, is_vip, channel_display) -> Image.Image:
    """'Ikki ustunli' — bright green sidebar + white content column."""
    width, height = 1200, 675
    img = Image.new("RGB", (width, height), CARD_BG)
    draw = ImageDraw.Draw(img)

    accent = GOLD if is_vip else BRIGHT_GREEN
    side_w = 420
    draw.rectangle([0, 0, side_w, height], fill=accent)

    pad = 40
    f_wordmark = _vf(SORA_PATH, 20, 800)
    mark_size = 28
    _hirely_logo(draw, pad, pad, mark_size, DARK_GREEN)
    draw.text((pad + mark_size + 9, pad + 3), "HIRELY JOBS", fill=DARK_GREEN, font=f_wordmark)

    f_sub = _vf(MANROPE_PATH, 14, 500)
    draw.text((pad, pad + 44), "Xayrli uchrashuvlar maskani", fill=SUBTITLE_GREEN, font=f_sub)

    if is_vip:
        f_badge = _vf(SORA_PATH, 15, 800)
        _vip_badge(draw, [side_w - 130, pad, side_w - 30, pad + 34], DARK_GREEN, accent, f_badge)

    f_hero = _vf(SORA_PATH, 40, 800)
    draw.text((pad, height - 220), "Yangi", fill=DARK_GREEN, font=f_hero)
    draw.text((pad, height - 220 + f_hero.size + 6), "vakansiya", fill=DARK_GREEN, font=f_hero)

    f_hero_sub = _vf(MANROPE_PATH, 14, 600)
    draw.text((pad, height - 60), "Tezkor ariza · Ishonchli taklif", fill=SUBTITLE_GREEN, font=f_hero_sub)

    # Right column
    rx = side_w + 52
    rw = width - rx - 52

    f_label = _vf(MANROPE_PATH, 12, 700)
    draw.text((rx, pad + 4), "LAVOZIM", fill=MUTED_GREEN, font=f_label)

    footer_y = height - pad - 26
    row_y = footer_y - 76
    f_title, title_lines = _wrap_fit(draw, position.upper(), [60, 48, 38], SORA_PATH, 800, rw, max_lines=2)
    title_h = sum(draw.textbbox((0, 0), l, font=f_title)[3] + 8 for l in title_lines)
    y_title = pad + 40 + max(0, (row_y - 40 - (pad + 40) - title_h) // 2)
    for line in title_lines:
        draw.text((rx, y_title), line, fill=DARK_GREEN, font=f_title)
        y_title += draw.textbbox((0, 0), line, font=f_title)[3] + 8

    f_chip_label = _vf(MANROPE_PATH, 11, 700)
    f_chip_val = _vf(SORA_PATH, 19, 600)
    col_gap = 48
    col_w = (rw - col_gap) // 2
    company_lines = _wrap(draw, company, f_chip_val, col_w, max_lines=1)
    f_salary, salary_lines = _wrap_fit(draw, salary, [19], SORA_PATH, 700, col_w, max_lines=1)

    draw.text((rx, row_y), "KOMPANIYA", fill=MUTED_GREEN, font=f_chip_label)
    for line in company_lines:
        draw.text((rx, row_y + 18), line, fill=DARK_GREEN, font=f_chip_val)

    sal_x = rx + col_w + col_gap
    draw.text((sal_x, row_y), "MAOSH", fill=MUTED_GREEN, font=f_chip_label)
    for line in salary_lines:
        sal_w = draw.textbbox((0, 0), line, font=f_salary)[2] + 24
        chip_box = [sal_x, row_y + 16, sal_x + sal_w, row_y + 16 + f_salary.size + 10]
        draw.rounded_rectangle(chip_box, radius=8, fill=accent)
        draw.text((sal_x + 12, row_y + 20), line, fill=DARK_GREEN, font=f_salary)

    draw.line([(rx, footer_y - 16), (width - 52, footer_y - 16)], fill=DIVIDER, width=1)
    f_footer = _vf(MANROPE_PATH, 13, 500)
    draw.text((rx, footer_y), f"t.me/{channel_display}", fill=MUTED_GREEN, font=f_footer)
    f_footer_r = _vf(MANROPE_PATH, 13, 600)
    r_text = "Hirely Jobs"
    r_w = draw.textbbox((0, 0), r_text, font=f_footer_r)[2]
    draw.text((width - 52 - r_w, footer_y), r_text, fill=MUTED_GREEN, font=f_footer_r)

    return img


def generate_vacancy_cover(
    position: str,
    company: str,
    salary: str,
    output_path: str,
    is_vip: bool = False,
    design: str = "A",
    channel_display: str = None,
) -> bool:
    """Generates a 1200x675 Hirely-branded cover image for a vacancy post.
    `design` picks between the two poster templates ("A" = framed/centered,
    "B" = two-column) — callers alternate them across posts."""
    try:
        channel = channel_display or os.environ.get("NUVI_TARGET_CHANNEL", "HirelyUz").lstrip("@")
        builder = _design_b if str(design).upper() == "B" else _design_a
        img = builder(position, company, salary, is_vip, channel)
        img.save(output_path, "PNG")
        logger.info(f"✅ Vacancy cover image saved successfully at: {output_path}")
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to generate vacancy cover image: {e}")
        return False
