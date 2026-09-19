import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hirely_links as hl  # noqa: E402


def test_parse_contact_variants():
    assert hl.parse_contact("@hr_person") == {"telegram": "hr_person"}
    assert hl.parse_contact("https://t.me/hr_person") == {"telegram": "hr_person"}
    assert hl.parse_contact("+998 90 123-45-67") == {"phone": "+998 90 123-45-67"}
    both = hl.parse_contact("Aloqa: @hr_person yoki +998901234567")
    assert both == {"telegram": "hr_person", "phone": "+998901234567"}
    assert hl.parse_contact("https://jobs.example.com/apply/1") == {"external_url": "https://jobs.example.com/apply/1"}
    assert hl.parse_contact("Kanalda ko'rsatilgan") == {}
    assert hl.parse_contact("") == {}


def test_category_guess():
    assert hl.guess_category("Senior Python developer") == "it"
    assert hl.guess_category("UI/UX dizayner") == "design"
    assert hl.guess_category("SMM menejer") == "marketing"
    assert hl.guess_category("Loyiha menejeri") == "digital"


def test_strip_contact_line_only_removes_the_contact():
    text = "📌 *Dev*\n\n💵 *Maosh:* 5 mln\n\n📩 *Aloqa:* @hr_person\n\n[Hirely Jobs](https://t.me/HirelyUz) - *slogan*\n"
    out = hl.strip_contact_line(text)
    assert "Aloqa" not in out and "@hr_person" not in out
    assert "Maosh" in out and "Hirely Jobs" in out and "\n\n\n" not in out
    assert hl.strip_contact_line("no contact here") == "no contact here\n"


def test_payload_marks_scraped_vs_user_and_skips_unparsable():
    v = {"id": 7, "user_id": 1, "title": "SMM menejer", "contact": "@smm_hr"}
    p = hl.build_payload(v)
    assert p["source"] == "scraper" and p["category"] == "marketing" and p["internal_reference"] == "vac-7"
    assert hl.build_payload(dict(v, user_id=55))["source"] == "bot"
    assert hl.build_payload(dict(v, contact="Kanalda ko'rsatilgan")) is None


def test_unconfigured_or_down_service_returns_none(monkeypatch):
    v = {"id": 1, "user_id": 5, "title": "Dev", "contact": "@hr_person"}
    monkeypatch.delenv("HIRELY_LINKS_URL", raising=False)
    monkeypatch.delenv("HIRELY_LINKS_TOKEN", raising=False)
    assert asyncio.run(hl.request_tracking_url(v)) is None
    monkeypatch.setenv("HIRELY_LINKS_URL", "http://127.0.0.1:9")  # nothing listens here
    monkeypatch.setenv("HIRELY_LINKS_TOKEN", "x" * 30)
    assert asyncio.run(hl.request_tracking_url(v)) is None
