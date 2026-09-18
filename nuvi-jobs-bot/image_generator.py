import html
import logging
import os
import shutil
import signal
import subprocess
import tempfile
import time

logger = logging.getLogger("jarvis.image_generator")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = {"A": "poster_a.html", "B": "poster_b.html"}
DEFAULT_TITLE_PX = {"A": 66, "B": 60}


def _chrome_bin() -> str:
    for cand in (
        os.environ.get("CHROMIUM_BIN"),
        shutil.which("chromium"),
        shutil.which("google-chrome"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ):
        if cand and os.path.exists(cand):
            return cand
    raise RuntimeError("Chromium topilmadi")


def _title_px(design: str, title: str) -> int:
    # Templates use one fixed size; only step down when a long title would
    # overflow the frame.
    base = DEFAULT_TITLE_PX[design]
    n = len(title)
    if n <= 24:
        return base
    if n <= 40:
        return round(base * 0.78)
    return round(base * 0.62)


def generate_vacancy_cover(
    position: str,
    company: str,
    salary: str,
    output_path: str,
    is_vip: bool = False,
    design: str = "A",
    channel_display: str = None,
) -> bool:
    """Renders one of the two Hirely poster templates (A = framed/centered,
    B = two-column) to a 1200x675 PNG via headless Chromium. Callers
    alternate `design` across posts. `is_vip` is accepted for call-site
    compatibility; the templates have no VIP variant."""
    try:
        design = "B" if str(design).upper() == "B" else "A"
        channel = channel_display or os.environ.get("NUVI_TARGET_CHANNEL", "HirelyUz").lstrip("@")

        with open(os.path.join(BASE_DIR, "templates", TEMPLATES[design]), encoding="utf-8") as f:
            page = f.read()
        page = (
            page.replace("{{FONT_DIR}}", "file://" + BASE_DIR)
            .replace("{{TITLE_SIZE}}", str(_title_px(design, position)))
            .replace("{{POSITION}}", html.escape(position))
            .replace("{{COMPANY}}", html.escape(company))
            .replace("{{SALARY}}", html.escape(salary))
            .replace("{{CHANNEL}}", html.escape(f"t.me/{channel}"))
        )

        with tempfile.TemporaryDirectory() as tmp:
            page_path = os.path.join(tmp, "poster.html")
            with open(page_path, "w", encoding="utf-8") as f:
                f.write(page)
            if os.path.exists(output_path):
                os.remove(output_path)
            cmd = [
                _chrome_bin(),
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                "--allow-file-access-from-files",
                "--window-size=1200,675",
                f"--user-data-dir={os.path.join(tmp, 'profile')}",
                f"--screenshot={output_path}",
                "file://" + page_path,
            ]
            # Chrome can write the screenshot yet linger (seen on macOS), so
            # stop waiting once the file is written and stable, then kill
            # the whole process group.
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            try:
                deadline = time.monotonic() + 30
                last_size = -1
                while time.monotonic() < deadline and proc.poll() is None:
                    size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                    if size > 0 and size == last_size:
                        break
                    last_size = size
                    time.sleep(0.4)
            finally:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

        ok = os.path.exists(output_path) and os.path.getsize(output_path) > 0
        if ok:
            logger.info(f"✅ Vacancy cover image saved successfully at: {output_path}")
        return ok
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to generate vacancy cover image: {e}")
        return False
