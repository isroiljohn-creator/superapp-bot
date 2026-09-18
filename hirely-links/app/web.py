import datetime as dt
import os
from typing import Any, Optional
from zoneinfo import ZoneInfo

from fastapi.templating import Jinja2Templates

from .config import get_settings

BASE = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE, "templates"))
_STATIC = os.path.join(BASE, "static")


def asset(path: str) -> str:
    try:
        v = int(os.path.getmtime(os.path.join(_STATIC, path)))
    except OSError:
        v = 0
    return f"/static/{path}?v={v}"


def num(v: Any) -> str:
    try:
        return f"{int(v):,}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


def pct(v: Optional[float], digits: int = 1) -> str:
    return f"{(v or 0):.{digits}f}%"


def local_dt(v: Optional[dt.datetime], fmt: str = "%d.%m.%Y %H:%M") -> str:
    if not v:
        return "—"
    return v.astimezone(ZoneInfo(get_settings().display_tz)).strftime(fmt)


def local_input(v: Optional[dt.datetime]) -> str:
    return local_dt(v, "%Y-%m-%dT%H:%M") if v else ""


templates.env.filters.update(num=num, pct=pct, local_dt=local_dt, local_input=local_input)
templates.env.globals.update(asset=asset)
