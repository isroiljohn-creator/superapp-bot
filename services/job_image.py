"""Generate branded NUVI Jobs vacancy banner images with Pillow.

Uses the NUVI Jobs template design:
- Light background with large "JOBS" watermark
- "NUVI_JOBS" header
- Vacancy title and salary in center
- nuvi logo at bottom
- Big Shoulders Text font (Google Fonts)
"""
import io
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont


# ── Paths ────────────────────────────────────────
_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.dirname(_DIR)
_ASSETS = os.path.join(_PROJECT, "assets")
_FONT_PATH = os.path.join(_ASSETS, "fonts", "BigShouldersText.ttf")
_TEMPLATE_PATH = os.path.join(_ASSETS, "jobs_template.png")

# ── Colors ───────────────────────────────────────
TEXT_DARK = (25, 25, 25)          # Near-black
TEXT_MEDIUM = (60, 60, 60)        # Dark gray for salary
WATERMARK = (230, 230, 230)       # Light gray for "JOBS" watermark
DOTS_COLOR = (210, 210, 210)      # Halftone dots
HEADER_COLOR = (25, 25, 25)       # "NUVI_JOBS" header


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Load Big Shoulders Text font, fall back to system fonts."""
    if os.path.exists(_FONT_PATH):
        try:
            font = ImageFont.truetype(_FONT_PATH, size)
            if bold:
                font.set_variation_by_name("ExtraBold")
            else:
                font.set_variation_by_name("SemiBold")
            return font
        except Exception:
            try:
                font = ImageFont.truetype(_FONT_PATH, size)
                font.set_variation_by_name("Black" if bold else "Bold")
                return font
            except Exception:
                pass

    # Fallback: system fonts
    fallbacks = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    for p in fallbacks:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_halftone_dots(draw, cx, cy, radius, dot_color, bg_size):
    """Draw a halftone dot pattern in a circular area."""
    spacing = 14
    max_dot_r = 5
    for x in range(max(0, cx - radius), min(bg_size[0], cx + radius), spacing):
        for y in range(max(0, cy - radius), min(bg_size[1], cy + radius), spacing):
            dist = ((x - cx)**2 + (y - cy)**2) ** 0.5
            if dist < radius:
                # Dots get smaller toward center
                ratio = dist / radius
                dot_r = int(max_dot_r * (0.3 + 0.7 * ratio))
                if dot_r > 0:
                    draw.ellipse(
                        [(x - dot_r, y - dot_r), (x + dot_r, y + dot_r)],
                        fill=dot_color,
                    )


def generate_vacancy_image(title: str, company: str = "", salary: str = "") -> io.BytesIO:
    """
    Generate a branded NUVI Jobs vacancy banner (1200×630).
    
    Design: Light background, large "JOBS" watermark, vacancy title + salary centered.
    Returns a BytesIO object with PNG data.
    """
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    # ── 1. Large "JOBS" watermark text ──
    watermark_font = _get_font(340, bold=True)
    wm_text = "JOBS"
    wm_bbox = draw.textbbox((0, 0), wm_text, font=watermark_font)
    wm_w = wm_bbox[2] - wm_bbox[0]
    wm_h = wm_bbox[3] - wm_bbox[1]
    draw.text(
        ((W - wm_w) // 2 - 40, (H - wm_h) // 2 - 40),
        wm_text, fill=WATERMARK, font=watermark_font,
    )

    # ── 2. Halftone dots pattern (bottom-left and right areas) ──
    _draw_halftone_dots(draw, 120, H - 100, 180, DOTS_COLOR, (W, H))
    _draw_halftone_dots(draw, W - 100, 100, 200, DOTS_COLOR, (W, H))

    # ── 3. "NUVI_JOBS" header (top center, italic-bold) ──
    header_font = _get_font(32, bold=True)
    header_text = "NUVI_JOBS"
    h_bbox = draw.textbbox((0, 0), header_text, font=header_font)
    h_w = h_bbox[2] - h_bbox[0]
    draw.text(((W - h_w) // 2, 35), header_text, fill=HEADER_COLOR, font=header_font)

    # ── 4. Vacancy title (CENTER, large, bold, dark) ──
    title_font = _get_font(80, bold=True)
    title_clean = title.strip().upper()

    # Word wrap for long titles
    wrapped = textwrap.fill(title_clean, width=22)
    lines = wrapped.split("\n")[:3]

    # Calculate total text block height
    line_height = 90
    total_text_h = len(lines) * line_height
    if salary:
        total_text_h += 55  # Space for salary line

    start_y = (H - total_text_h) // 2

    for line in lines:
        line_bbox = draw.textbbox((0, 0), line, font=title_font)
        line_w = line_bbox[2] - line_bbox[0]
        draw.text(((W - line_w) // 2, start_y), line, fill=TEXT_DARK, font=title_font)
        start_y += line_height

    # ── 5. Salary (below title, centered, slightly smaller) ──
    if salary:
        salary_font = _get_font(42, bold=False)
        salary_text = salary.strip()
        s_bbox = draw.textbbox((0, 0), salary_text, font=salary_font)
        s_w = s_bbox[2] - s_bbox[0]
        draw.text(((W - s_w) // 2, start_y + 10), salary_text, fill=TEXT_MEDIUM, font=salary_font)

    # ── 6. NUVI logo at bottom center (from image file) ──
    _logo_path = os.path.join(_ASSETS, "nuvi_logo.png")
    if os.path.exists(_logo_path):
        try:
            logo = Image.open(_logo_path).convert("RGBA")
            # Scale logo to height ~70px, keep aspect ratio
            logo_target_h = 70
            ratio = logo_target_h / logo.height
            logo_w = int(logo.width * ratio)
            logo = logo.resize((logo_w, logo_target_h), Image.Resampling.LANCZOS)
            # Center horizontally, place near bottom
            logo_x = (W - logo_w) // 2
            logo_y = H - logo_target_h - 20
            # Paste with alpha mask for transparency
            img.paste(logo, (logo_x, logo_y), logo)
        except Exception:
            # Fallback: text if logo image fails
            logo_font = _get_font(38, bold=True)
            l_bbox = draw.textbbox((0, 0), "nuvi", font=logo_font)
            l_w = l_bbox[2] - l_bbox[0]
            draw.text(((W - l_w) // 2, H - 65), "nuvi", fill=TEXT_DARK, font=logo_font)
    else:
        logo_font = _get_font(38, bold=True)
        l_bbox = draw.textbbox((0, 0), "nuvi", font=logo_font)
        l_w = l_bbox[2] - l_bbox[0]
        draw.text(((W - l_w) // 2, H - 65), "nuvi", fill=TEXT_DARK, font=logo_font)

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf
