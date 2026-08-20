# Telegram Bot Setup

Alerts are sent to a Telegram chat you control. The scanner never reads
from Telegram or accepts commands through it — it's alert-only, one
direction.

## Steps

1. **Create a bot.** In Telegram, message **@BotFather**, send `/newbot`,
   follow the prompts. You'll get a bot token that looks like
   `123456789:AAExampleTokenDoNotShare`.
2. **Start a chat with your bot.** Search for your bot's username in
   Telegram and send it any message (e.g. "hi") so Telegram knows you've
   opened a chat with it.
3. **Get your chat ID:**
   ```
   python scripts/get_telegram_chat_id.py
   ```
   This calls Telegram's `getUpdates` API using the token in your `.env`
   and prints the chat ID from your most recent message to the bot.
4. **Fill in `.env`:**
   ```
   TELEGRAM_BOT_TOKEN=123456789:AAExampleTokenDoNotShare
   TELEGRAM_CHAT_ID=987654321
   ```
5. **Send a test alert:**
   ```
   python -m scanner.main --test-telegram
   ```

Keep the token out of version control — it's in `.env`, which is
gitignored. If it ever leaks, revoke it via @BotFather (`/revoke`) and
generate a new one.
