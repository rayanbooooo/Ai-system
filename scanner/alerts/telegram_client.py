"""Minimal Telegram Bot API client. Send-only - never reads/accepts
commands. See docs/TELEGRAM_SETUP.md for how to create the bot and get a
chat id.
"""
from __future__ import annotations

import requests


class TelegramClient:
    def __init__(self, settings) -> None:
        self._token = settings.bot_token
        self._chat_id = settings.chat_id

    def send_message(self, text: str) -> None:
        if not self._token or not self._chat_id:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are not set - see docs/TELEGRAM_SETUP.md"
            )
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        resp = requests.post(url, json={"chat_id": self._chat_id, "text": text}, timeout=10)
        resp.raise_for_status()
