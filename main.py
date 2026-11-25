import asyncio
from datetime import datetime, timedelta, timezone
import os
from threading import Thread
from flask import Flask
import httpx
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- 1. DUMMY WEB SERVER TO KEEP RENDER AWAKE ---
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive and running!", 200


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)


Thread(target=run_flask, daemon=True).start()

# --- 2. CONFIGURATION & CREDENTIALS ---
API_ID = int(os.environ.get("API_ID", "36958065"))
API_HASH = os.environ.get("API_HASH", "5fa9f963c45b1bd24f1944f83ed70a1f")

SESSION_STRING = os.environ.get(
    "SESSION_STRING",
    "1BJWap1sBu1pGpyWbxEuPvpEDGQRfxUEK8tHampQFUJIY41b0tWFhKEvFsrd1JgLxIdM97rIOYAhbATkTH3l0Y0yi0_3Q-4V1CPNHm1OhBChrmsSrxFViSmjIeGl59nAxshF_ej8W66V8Hr_67sz39hxXSv1NGY3zD_gl36oYd7R2VPpKQBhgtwrSJ_YSI9Fb03SFRF80X6bWjeysARtKpHu_w0S1x3x3cnHoU8CXM4gM6G4djycoo1TMQue4p-FUTS2oYm5fhYVKhJE2hvk_77NFDn5OfNZM4ROB066cj0emQFCMYQwYtavITErNo0-vgSCViGkY7anoFvGj1pZt3klwEqGj4Y8=",
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "5821223676:AAFNcEr4xSk6Iv1TPFfPcqOUfFsYKhB8-NA")
CHAT_ID = os.environ.get("CHAT_ID", "6677697222")

# Your 10 target channels
CHANNELS = [
    -1003955016580,
    -1004323860533,
    -1003749032282,
    -1004429521400,
    -1003984618284,
    -1004473788210,
    -1003511130962,
    -1004430225885,
    -1003980795890,
    -1003840464649,
]

# Core text match (handles optional trailing exclamation mark on bonus line)
TARGET_CORE = """🚨 ATTENTION! SIGNAL PREPARING 🚨

⏰ Entry opportunity approaching...
🔍 Waiting for confirmation...

🎁 PROMO CODE: LUX10
💰 Use code to earn bonus"""

WAT_TZ = timezone(timedelta(hours=1))  # Nigeria time (UTC+1)
TARGET_MINUTES = 10

# Stores list of {"minute_time": datetime, "link": str} per channel
preparing_history = {}

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


def to_wat_minute(dt: datetime | None) -> datetime:
    """Converts a datetime to Nigeria time (WAT, UTC+1) floored to the minute."""
    base = dt or datetime.now(WAT_TZ)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    return base.astimezone(WAT_TZ).replace(second=0, microsecond=0)


def build_message_link(chat, message_id: int) -> str:
    if getattr(chat, "username", None):
        return f"https://t.me/{chat.username}/{message_id}"
    clean_id = str(chat.id).replace("-100", "")
    return f"https://t.me/c/{clean_id}/{message_id}"


async def send_bot_notification(text: str):
    """Sends the formatted alert to your private chat via your Telegram Bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    async with httpx.AsyncClient(timeout=15.0) as http_client:
        try:
            resp = await http_client.post(url, json=payload)
            resp.raise_for_status()
        except Exception as e:
            print(f"Failed to send bot notification: {e}", flush=True)


@client.on(events.NewMessage(chats=CHANNELS))
async def handle_message(event):
    message_text = (event.raw_text or "").strip()

    # Ignore every message except SIGNAL PREPARING
    if TARGET_CORE.strip() not in message_text:
        return

    chat = await event.get_chat()
    chat_id = chat.id
    chat_title = getattr(chat, "title", str(chat_id))

    current_minute_dt = to_wat_minute(event.date)
    current_link = build_message_link(chat, event.id)

    # Keep only entries from the last 15 minutes (in minutes) for this channel
    cutoff = current_minute_dt - timedelta(minutes=15)
    history = [
        item for item in preparing_history.get(chat_id, [])
        if item["minute_time"] >= cutoff
    ]

    # Check if any earlier SIGNAL PREPARING happened exactly 10 minutes earlier
    matched_earlier = None
    for item in history:
        diff_minutes = int((current_minute_dt - item["minute_time"]).total_seconds() // 60)
        if diff_minutes == TARGET_MINUTES:
            matched_earlier = (item, diff_minutes)
            break

    # Save current SIGNAL PREPARING minute timestamp into channel history
    history.append({"minute_time": current_minute_dt, "link": current_link})
    preparing_history[chat_id] = history

    if matched_earlier is not None:
        prev_item, gap_mins = matched_earlier
        formatted_now = datetime.now(WAT_TZ).strftime("%I:%M %p")

        alert_text = (
            f"🎯 10-MINUTE SIGNAL PREPARING HIT! 🎯\n"
            f"Channel: {chat_title}\n"
            f"Alert Time: {formatted_now} WAT\n"
            f"Time Gap: {gap_mins} min\n"
            f"🔗 1st Signal Link: {prev_item['link']}\n"
            f"🔗 10-Min Signal Link: {current_link}"
        )

        print(alert_text, flush=True)
        await send_bot_notification(alert_text)


async def main():
    print("Starting Telegram userbot...", flush=True)
    await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError(
            "SESSION_STRING is invalid or expired. Generate a new StringSession and redeploy."
        )
    print(
        "Userbot authorized: alerting when SIGNAL PREPARING repeats 10 min later (WAT)...",
        flush=True,
    )
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"Fatal startup error: {exc}", flush=True)
        raise
