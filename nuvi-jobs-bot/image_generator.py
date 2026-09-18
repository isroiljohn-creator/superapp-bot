from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import logging

logger = logging.getLogger("jarvis.image_generator")

# Formora-inspired palette: warm rust/orange canvas, bold black wordmark,
# cream hero card, dark stat strip. VIP swaps the accent for gold.
ORANGE = (232, 92, 30)
ORANGE_DEEP = (140, 46, 12)
CREAM = (247, 240, 231)
INK = (26, 20, 15)
GOLD = (222, 168, 66)


def _radial_bg(width: int, height: int, center_color, edge_color, center=None) -> Image.Image:
    """Warm radial gradient canvas (Formora's textured orange background).
    Builds the gradient as a grayscale mask and uses it to blend two solid
    layers in C (Image.composite) — a pure-Python per-pixel loop over
    800k+ pixels would take many seconds."""
    grad = Image.radial_gradient("L").resize((width * 2, height * 2))
    cx = center or (width, int(height * 0.35))
    mask = grad.crop((width - cx[0], height - cx[1], width - cx[0] + width, height - cx[1] + height))
    center_layer = Image.new("RGB", (width, height), center_color)
    edge_layer = Image.new("RGB", (width, height), edge_color)
    return Image.composite(center_layer, edge_layer, mask)


def _accent_flower(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, color) -> None:
    """Small 6-petal burst — the orange asterisk accent from the reference logo."""
    import math
    petal_r = r * 0.55
    for i in range(6):
        angle = math.radians(i * 60)
        px = cx + math.cos(angle) * r * 0.55
        py = cy + math.sin(angle) * r * 0.55
        draw.ellipse([px - petal_r, py - petal_r, px + petal_r, py + petal_r], fill=color)
    draw.ellipse([cx - petal_r, cy - petal_r, cx + petal_r, cy + petal_r], fill=color)


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


def _wrap_fit(draw, text, font_sizes, font_path, max_width, max_lines=2):
    """Wraps at the largest font size (in descending order) that fits the
    whole text within max_lines — falls back to smaller sizes instead of
    silently dropping words, and to the smallest size (with a hard cut) if
    even that doesn't fit."""
    word_count = len(text.split())
    chosen_font, chosen_lines = None, None
    for size in font_sizes:
        font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
        lines = _wrap(draw, text, font, max_width, max_lines=max_lines)
        chosen_font, chosen_lines = font, lines
        if sum(len(line.split()) for line in lines) >= word_count:
            break
    return chosen_font, chosen_lines


def generate_vacancy_cover(position: str, company: str, salary: str, output_path: str, is_vip: bool = False) -> bool:
    """
    Generates a bold, premium 1200x675 cover image for a vacancy post,
    styled after a warm orange/black editorial reference: a cream "hero"
    card with a huge bold job title up top, and a dark stat-strip footer
    with the company/salary called out like highlight chips.
    """
    try:
        width, height = 1200, 675
        accent = GOLD if is_vip else ORANGE

        img = _radial_bg(width, height, ORANGE if not is_vip else (74, 58, 22), ORANGE_DEEP if not is_vip else (20, 16, 10))
        img = img.convert("RGBA")
        draw = ImageDraw.Draw(img)

        if is_vip:
            draw.rectangle([0, 0, width - 1, height - 1], outline=GOLD, width=10)
            draw.rectangle([16, 16, width - 17, height - 17], outline=(255, 255, 255, 60), width=1)

        font_dir = os.path.dirname(os.path.abspath(__file__))
        bold_path = os.path.join(font_dir, "Inter-Bold.ttf")
        reg_path = os.path.join(font_dir, "Inter-Regular.ttf")
        have_fonts = os.path.exists(bold_path) and os.path.exists(reg_path)

        if have_fonts:
            font_logo = ImageFont.truetype(bold_path, 24)
            font_eyebrow = ImageFont.truetype(bold_path, 15)
            font_title = ImageFont.truetype(bold_path, 58)
            font_chip_label = ImageFont.truetype(bold_path, 16)
            font_chip_val = ImageFont.truetype(bold_path, 27)
            font_footer = ImageFont.truetype(reg_path, 20)
            font_badge = ImageFont.truetype(bold_path, 18)
        else:
            logger.warning("Inter fonts not found, falling back to default.")
            font_logo = font_eyebrow = font_title = font_chip_label = font_chip_val = font_footer = font_badge = ImageFont.load_default()

        margin = 40
        col_width = (width - 2 * margin) // 2 - 80
        company_lines = _wrap(draw, company, font_chip_val, col_width, max_lines=2)
        # Salary is the visual highlight (big bold number) — try progressively
        # smaller sizes so a long free-text salary never loses words instead
        # of just always wrapping at a huge size and cutting it off.
        font_chip_val_salary, salary_lines = _wrap_fit(
            draw, salary, [42, 34, 27, 22], bold_path if have_fonts else None, col_width, max_lines=2
        )
        company_row_h = font_chip_val.size + 6
        salary_row_h = font_chip_val_salary.size + 6
        # Strip grows to fit whichever column's wrapped text runs taller (and
        # the hero card shrinks to match), so a long company name or salary
        # string that needs a second line never collides with the footer.
        content_h = max(len(company_lines) * company_row_h, len(salary_lines) * salary_row_h)
        strip_height = 150 + max(0, content_h - company_row_h)
        strip_top = height - margin - strip_height
        hero_box = [margin, margin, width - margin, strip_top - 20]
        draw.rounded_rectangle(hero_box, radius=28, fill=CREAM)

        # Logo row: orange asterisk + NUVI JOBS wordmark
        _accent_flower(draw, margin + 46, margin + 50, 20, accent)
        draw.text((margin + 78, margin + 36), "NUVI", fill=INK, font=font_logo)
        w_nuvi = draw.textbbox((0, 0), "NUVI", font=font_logo)[2]
        draw.text((margin + 78 + w_nuvi + 10, margin + 36), "JOBS", fill=accent, font=font_logo)

        if is_vip:
            badge_box = [width - margin - 110, margin + 22, width - margin - 20, margin + 58]
            draw.rounded_rectangle(badge_box, radius=18, fill=accent)
            draw.text((badge_box[0] + 18, badge_box[1] + 8), "★ VIP", fill=INK, font=font_badge)

        # Thin eyebrow row (Formora's 3-label strip, adapted)
        eyebrow_y = margin + 92
        eyebrow_items = ["YANGI VAKANSIYA", "TEZKOR ARIZA", "ISHONCHLI TAKLIF"]
        ex = margin + 46
        for i, item in enumerate(eyebrow_items):
            draw.text((ex, eyebrow_y), item, fill=(120, 108, 96), font=font_eyebrow)
            w = draw.textbbox((0, 0), item, font=font_eyebrow)[2]
            ex += w + 24
            if i < len(eyebrow_items) - 1:
                draw.line([(ex - 14, eyebrow_y + 8), (ex - 6, eyebrow_y + 8)], fill=(190, 178, 164), width=2)

        # Big bold job title — the wordmark-style headline
        title_lines = _wrap(draw, position.upper(), font_title, hero_box[2] - hero_box[0] - 92, max_lines=2)
        y_title = 235 if len(title_lines) == 2 else 270
        for line in title_lines:
            draw.text((margin + 46, y_title), line, fill=INK, font=font_title)
            h = draw.textbbox((0, 0), line, font=font_title)[3]
            y_title += h + 8

        # Dark/orange stat-strip footer with company + salary chips
        strip_box = [margin, strip_top, width - margin, height - margin]
        draw.rounded_rectangle(strip_box, radius=28, fill=(*INK, 235))

        chip_y = strip_box[1] + 30
        col1_x = strip_box[0] + 46
        col2_x = strip_box[0] + (strip_box[2] - strip_box[0]) // 2 + 20

        draw.text((col1_x, chip_y), "KOMPANIYA", fill=accent, font=font_chip_label)
        cy = chip_y + 28
        for line in company_lines:
            draw.text((col1_x, cy), line, fill=CREAM, font=font_chip_val)
            cy += draw.textbbox((0, 0), line, font=font_chip_val)[3] + 6

        draw.line([(col2_x - 24, chip_y), (col2_x - 24, strip_box[3] - 26)], fill=(90, 78, 66), width=1)

        draw.text((col2_x, chip_y), "MAOSH", fill=accent, font=font_chip_label)
        sy = chip_y + 28
        for line in salary_lines:
            draw.text((col2_x, sy), line, fill=(120, 230, 150), font=font_chip_val_salary)
            sy += draw.textbbox((0, 0), line, font=font_chip_val_salary)[3] + 6

        footer_y = strip_box[3] - 34
        draw.text((strip_box[0] + 46, footer_y), "t.me/nuvi_jobs", fill=(150, 138, 124), font=font_footer)
        footer_r = "NUVI AI Agency"
        w_r = draw.textbbox((0, 0), footer_r, font=font_footer)[2]
        draw.text((strip_box[2] - 46 - w_r, footer_y), footer_r, fill=(150, 138, 124), font=font_footer)

        img.convert("RGB").save(output_path, "PNG")
        logger.info(f"✅ Vacancy cover image saved successfully at: {output_path}")
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to generate vacancy cover image: {e}")
        return False
