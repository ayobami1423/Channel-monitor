import asyncio
from datetime import datetime
import os
import re
from threading import Thread
from flask import Flask
import httpx
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- 1. DUMMY WEB SERVER TO KEEP CLOUD HOSTING AWAKE ---
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

# Stores {"step": int, "link": str} for the previous qualifying Martingale win per channel
last_martingale_win = {}

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


def extract_qualifying_martingale_step(text: str):
    """
    Returns Martingale step (int) if it is MARTINGALE 2 or higher.
    Returns None for MARTINGALE 1, DIRECT wins, or non-Martingale wins.
    """
    upper_text = text.upper()
    if "(WIN (DIRECT))" in upper_text or "MARTINGALE" not in upper_text:
        return None

    match = re.search(r"MARTINGALE\s+(\d+)", text, flags=re.IGNORECASE)
    if match:
        step = int(match.group(1))
        if step >= 2:
            return step
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
    chat = await event.get_chat()
    chat_id = chat.id
    chat_title = getattr(chat, "title", str(chat_id))

    is_mega_win = "🚀 MEGA WIN!" in message_text
    is_normal_win = "🎉 YOU WON!" in message_text
    is_win = is_mega_win or is_normal_win

    if is_win:
        step = extract_qualifying_martingale_step(message_text)

        if step is not None:
            current_link = build_message_link(chat, event.id)
            prev_win = last_martingale_win.get(chat_id)

            # Store latest qualifying Martingale win for future comparisons
            last_martingale_win[chat_id] = {"step": step, "link": current_link}

            if prev_win is not None:
                current_time = datetime.now()
                formatted_time = current_time.strftime("%I:%M %p")

                alert_text = (
                    f"🔥 BACK-TO-BACK MARTINGALE ALERT! 🔥\n"
                    f"Channel: {chat_title}\n"
                    f"Time: {formatted_time}\n"
                    f"Sequence: Martingale {prev_win['step']} → Martingale {step}\n"
                    f"🔗 1st Win Link: {prev_win['link']}\n"
                    f"🔗 2nd Win Link: {current_link}\n\n"
                    f"{message_text}"
                )

                print(alert_text, flush=True)
                await send_bot_notification(alert_text)
        else:
            # Direct win or Martingale 1 resets any active streak
            last_martingale_win[chat_id] = None
    elif "❌ LOSS" in message_text:
        # Reset consecutive Martingale tracking after a loss
        last_martingale_win[chat_id] = None


async def main():
    print("Starting Telegram userbot...", flush=True)
    await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError(
            "SESSION_STRING is invalid or expired. Generate a new StringSession and redeploy."
        )
    print(
        "Userbot authorized and listening for consecutive Martingale (2+) wins...",
        flush=True,
    )
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"Fatal startup error: {exc}", flush=True)
        raise
