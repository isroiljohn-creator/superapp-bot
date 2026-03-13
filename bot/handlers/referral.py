"""Referral handler — referral-related utilities (no slash commands).

All user-facing referral/profile/help interactions are handled via
menu buttons in menu.py. This module is kept for any shared utility
functions that may be needed by other handlers.
"""
from aiogram import Router

router = Router(name="referral")
