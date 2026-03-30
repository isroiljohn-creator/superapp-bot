"""Generate branded vacancy banner images with Pillow."""
import io
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont


# ── Paths ────────────────────────────────────────
_DIR = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.join(os.path.dirname(_DIR), "assets")
_LOGO_PATH = os.path.join(_ASSETS, "nuvi_logo.png")

# ── Colors ───────────────────────────────────────
BG_GRADIENT_TOP = (15, 23, 42)       # Dark navy
BG_GRADIENT_BOTTOM = (30, 58, 138)   # Deep blue
ACCENT = (99, 102, 241)              # Indigo accent
TEXT_WHITE = (255, 255, 255)
TEXT_LIGHT = (203, 213, 225)         # Slate-300
BADGE_BG = (99, 102, 241, 200)      # Semi-transparent indigo


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try to load a good font, fall back to default."""
    font_candidates = [
        # Common on Linux/Railway
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_gradient(draw: ImageDraw.Draw, width: int, height: int):
    """Draw a vertical gradient background."""
    for y in range(height):
        ratio = y / height
        r = int(BG_GRADIENT_TOP[0] + (BG_GRADIENT_BOTTOM[0] - BG_GRADIENT_TOP[0]) * ratio)
        g = int(BG_GRADIENT_TOP[1] + (BG_GRADIENT_BOTTOM[1] - BG_GRADIENT_TOP[1]) * ratio)
        b = int(BG_GRADIENT_TOP[2] + (BG_GRADIENT_BOTTOM[2] - BG_GRADIENT_TOP[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def generate_vacancy_image(title: str, company: str = "", salary: str = "") -> io.BytesIO:
    """
    Generate a branded vacancy banner (1200×630).
    
    Returns a BytesIO object with PNG data.
    """
    W, H = 1200, 630
    img = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(img)

    # 1. Gradient background
    _draw_gradient(draw, W, H)

    # 2. Decorative elements
    # Top-right accent circle
    draw.ellipse([(W - 250, -100), (W + 50, 200)], fill=(99, 102, 241, 40))
    # Bottom-left accent circle
    draw.ellipse([(-100, H - 200), (200, H + 50)], fill=(99, 102, 241, 30))

    # 3. "NUVI JOBS" badge at top
    badge_font = _get_font(22, bold=True)
    badge_text = "NUVI JOBS"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_w = badge_bbox[2] - badge_bbox[0] + 40
    badge_h = badge_bbox[3] - badge_bbox[1] + 16
    badge_x = 60
    badge_y = 50
    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)],
        radius=badge_h // 2,
        fill=ACCENT,
    )
    draw.text(
        (badge_x + 20, badge_y + 6),
        badge_text, fill=TEXT_WHITE, font=badge_font,
    )

    # 4. Vacancy title (main text) — wrap long titles
    title_font = _get_font(52, bold=True)
    title_clean = title.strip()
    
    # Word wrap
    wrapped = textwrap.fill(title_clean, width=28)
    lines = wrapped.split("\n")[:3]  # Max 3 lines
    
    title_y = 130
    for line in lines:
        draw.text((60, title_y), line, fill=TEXT_WHITE, font=title_font)
        title_y += 65

    # 5. "KERAK" label under title
    kerak_font = _get_font(36, bold=False)
    kerak_y = title_y + 10
    draw.text((60, kerak_y), "kerak", fill=TEXT_LIGHT, font=kerak_font)

    # 6. Company & salary info
    info_font = _get_font(28, bold=False)
    info_y = kerak_y + 60

    if company:
        draw.text((60, info_y), f"Kompaniya:  {company}", fill=TEXT_LIGHT, font=info_font)
        info_y += 40

    if salary:
        draw.text((60, info_y), f"Maosh:  {salary}", fill=TEXT_LIGHT, font=info_font)

    # 7. Decorative line
    draw.rectangle([(60, H - 120), (W - 60, H - 118)], fill=(99, 102, 241, 80))

    # 8. NUVI logo at bottom center
    try:
        if os.path.exists(_LOGO_PATH):
            logo = Image.open(_LOGO_PATH).convert("RGBA")
            # Scale logo to height ~60px
            logo_h = 60
            ratio = logo_h / logo.height
            logo_w = int(logo.width * ratio)
            logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
            logo_x = (W - logo_w) // 2
            logo_y = H - 90
            img.paste(logo, (logo_x, logo_y), logo)
    except Exception:
        # Fallback: text "NUVI" if logo fails
        nuvi_font = _get_font(32, bold=True)
        nuvi_bbox = draw.textbbox((0, 0), "NUVI", font=nuvi_font)
        nuvi_w = nuvi_bbox[2] - nuvi_bbox[0]
        draw.text(((W - nuvi_w) // 2, H - 80), "NUVI", fill=TEXT_LIGHT, font=nuvi_font)

    # Convert to RGB for JPEG-compatible PNG
    final = Image.new("RGB", (W, H))
    final.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)

    buf = io.BytesIO()
    final.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf
