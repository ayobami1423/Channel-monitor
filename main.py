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

PREPARING_BLOCK = """🚨 ATTENTION! SIGNAL PREPARING 🚨

⏰ Entry opportunity approaching...
🔍 Waiting for confirmation...

🎁 PROMO CODE: LUX10
💰 Use code to earn bonus!"""

CANCELLED_BLOCK = """❌ SIGNAL CANCELLED

🔄 Analysis continuing...
⏳ Waiting for new signal..."""

CONFIRMED_HEADER = "✅ SIGNAL CONFIRMED! 🚀"
CONFIRMED_FOOTER = "⚠️ MAXIMUM 5 MARTINGALES"

WAT_TZ = timezone(timedelta(hours=1))  # Nigeria time (UTC+1)

# Per-channel state:
# {"streak": int, "pending_preparing": bool, "last_preparing_link": str | None}
channel_states = {}

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


def get_channel_state(chat_id: int) -> dict:
    if chat_id not in channel_states:
        channel_states[chat_id] = {
            "streak": 0,
            "pending_preparing": False,
            "last_preparing_link": None,
        }
    return channel_states[chat_id]


def classify_message(text: str) -> str | None:
    """Returns 'preparing', 'confirmed', 'cancelled', or None for any other message."""
    if PREPARING_BLOCK in text:
        return "preparing"
    if CANCELLED_BLOCK in text:
        return "cancelled"
    if CONFIRMED_HEADER in text and CONFIRMED_FOOTER in text:
        return "confirmed"
    return None


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
    msg_type = classify_message(message_text)

    # Ignore every message except PREPARING, CONFIRMED, and CANCELLED
    if msg_type is None:
        return

    chat = await event.get_chat()
    chat_id = chat.id
    chat_title = getattr(chat, "title", str(chat_id))
    msg_link = build_message_link(chat, event.id)
    now_wat = datetime.now(WAT_TZ).strftime("%I:%M %p")
    state = get_channel_state(chat_id)

    if msg_type == "preparing":
        state["pending_preparing"] = True
        state["last_preparing_link"] = msg_link
        print(
            f"[{chat_title}] SIGNAL PREPARING recorded (Current Streak: {state['streak']})",
            flush=True,
        )

    elif msg_type == "confirmed":
        if state["pending_preparing"]:
            state["streak"] += 1
            state["pending_preparing"] = False
            prep_link = state["last_preparing_link"]
            current_streak = state["streak"]

            alert_text = (
                f"🔥 CONFIRMED STREAK: {current_streak} 🔥\n"
                f"Channel: {chat_title}\n"
                f"Time: {now_wat} WAT\n"
                f"🔗 Preparing Link: {prep_link}\n"
                f"🔗 Confirmed Link: {msg_link}"
            )
            print(alert_text, flush=True)
            await send_bot_notification(alert_text)

    elif msg_type == "cancelled":
        if state["pending_preparing"] or state["streak"] > 0:
            prev_streak = state["streak"]
            prep_link = state["last_preparing_link"]
            state["streak"] = 0
            state["pending_preparing"] = False
            state["last_preparing_link"] = None

            alert_text = (
                f"🛑 SIGNAL CANCELLED — STREAK RESET TO 0 🛑\n"
                f"Channel: {chat_title}\n"
                f"Time: {now_wat} WAT\n"
                f"Previous Streak: {prev_streak} → 0\n"
                f"🔗 Preparing Link: {prep_link or 'N/A'}\n"
                f"🔗 Cancelled Link: {msg_link}"
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
        "Userbot authorized: tracking PREPARING → CONFIRMED streaks and CANCELLED resets (WAT)...",
        flush=True,
    )
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"Fatal startup error: {exc}", flush=True)
        raise
