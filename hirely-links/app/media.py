import hashlib
import io
import os
from typing import Tuple

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_W = 1200
SMALL_W = 600
MAX_PIXELS = 40_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class MediaError(ValueError):
    pass


def _save(img: Image.Image, path: str, width: int) -> Tuple[int, int]:
    if img.width > width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    img.save(path + ".tmp", "WEBP", quality=82, method=6)
    os.replace(path + ".tmp", path)
    return img.width, img.height


def process_banner(data: bytes, media_dir: str, max_bytes: int) -> Tuple[str, int, int]:
    """Validates by decoding (never trusts the client's content type), re-encodes to WebP (drops EXIF),
    and writes a 1200px and a 600px variant named after the content hash."""
    if len(data) > max_bytes:
        raise MediaError(f"Rasm hajmi {max_bytes // 1024 // 1024} MB dan oshmasligi kerak")
    try:
        img = Image.open(io.BytesIO(data))
        if img.format not in ("JPEG", "PNG", "WEBP"):
            raise MediaError("Faqat JPEG, PNG yoki WebP")
        img.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        raise MediaError("Rasm faylini o'qib bo'lmadi")
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") and "transparency" in img.info or img.mode in ("RGBA", "LA") else "RGB")
    name = hashlib.sha256(data).hexdigest()[:24]
    os.makedirs(media_dir, exist_ok=True)
    w, h = _save(img, os.path.join(media_dir, f"{name}.webp"), MAX_W)
    _save(img, os.path.join(media_dir, f"{name}-s.webp"), SMALL_W)
    return name, w, h
