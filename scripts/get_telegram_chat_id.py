#!/usr/bin/env python3
"""Prints the chat ID for your most recent message to your Telegram bot.

Run this after messaging your bot at least once (see
docs/TELEGRAM_SETUP.md). Requires TELEGRAM_BOT_TOKEN in .env.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Set TELEGRAM_BOT_TOKEN in .env first (see docs/TELEGRAM_SETUP.md).", file=sys.stderr)
        return 1

    resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
    resp.raise_for_status()
    updates = resp.json().get("result", [])
    if not updates:
        print("No messages found yet - send your bot a message in Telegram first, then re-run this.")
        return 1

    last = updates[-1]
    chat = last.get("message", {}).get("chat", {})
    chat_id = chat.get("id")
    title = chat.get("title") or chat.get("username") or chat.get("first_name")
    print(f"Chat ID: {chat_id}  ({title})")
    print("Add this to .env as TELEGRAM_CHAT_ID.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
