import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask
import httpx
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- 1. DUMMY WEB SERVER TO KEEP CLOUD HOSTING AWAKE ---
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive and running!"


def run_flask():
    app.run(host="0.0.0.0", port=8080)


Thread(target=run_flask, daemon=True).start()

# --- 2. CONFIGURATION & CREDENTIALS ---
API_ID = 36958065
API_HASH = "5fa9f963c45b1bd24f1944f83ed70a1f"

SESSION_STRING = "1BJWap1sBu1pGpyWbxEuPvpEDGQRfxUEK8tHampQFUJIY41b0tWFhKEvFsrd1JgLxIdM97rIOYAhbATkTH3l0Y0yi0_3Q-4V1CPNHm1OhBChrmsSrxFViSmjIeGl59nAxshF_ej8W66V8Hr_67sz39hxXSv1NGY3zD_gl36oYd7R2VPpKQBhgtwrSJ_YSI9Fb03SFRF80X6bWjeysARtKpHu_w0S1x3x3cnHoU8CXM4gM6G4djycoo1TMQue4p-FUTS2oYm5fhYVKhJE2hvk_77NFDn5OfNZM4ROB066cj0emQFCMYQwYtavITErNo0-vgSCViGkY7anoFvGj1pZt3klwEqGj4Y8="

BOT_TOKEN = "5821223676:AAFNcEr4xSk6Iv1TPFfPcqOUfFsYKhB8-NA"
CHAT_ID = "6677697222"

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

# Exact message template to watch for
TARGET_MESSAGE = """🚨 ATTENTION! SIGNAL PREPARING 🚨

⏰ Entry opportunity approaching...
🔍 Waiting for confirmation...

🎁 PROMO CODE: LUX10
💰 Use code to earn bonus!"""

# Dictionary to store timestamp and gap history per channel
channel_history = {}

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


async def send_bot_notification(text: str):
    """Sends the formatted alert to your private chat via your Telegram Bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    async with httpx.AsyncClient() as http_client:
        try:
            await http_client.post(url, json=payload)
        except Exception as e:
            print(f"Failed to send bot notification: {e}", flush=True)


@client.on(events.NewMessage(chats=CHANNELS))
async def handle_message(event):
    message_text = event.raw_text.strip()

    # Strictly ignore any message that doesn't match the target format
    if message_text != TARGET_MESSAGE.strip():
        return

    chat = await event.get_chat()
    chat_id = chat.id
    chat_title = getattr(chat, "title", str(chat_id))

    current_time = datetime.now()
    formatted_time = current_time.strftime("%I:%M %p")  # 12-hour format AM/PM

    if chat_id in channel_history:
        prev_time = channel_history[chat_id]["last_time"]
        prev_gap = channel_history[chat_id].get("last_gap")

        # Calculate exact gap based strictly on minute values (ignoring seconds)
        current_gap = (current_time.hour * 60 + current_time.minute) - (
            prev_time.hour * 60 + prev_time.minute
        )

        # Check if the minute gap occurred twice in a row for this channel
        if prev_gap is not None and current_gap == prev_gap:
            alert_text = (
                f"⚠️ REPEATED INTERVAL DETECTED ⚠️\n"
                f"Channel: {chat_title}\n"
                f"Time: {formatted_time}\n"
                f"Interval Pattern: {current_gap} mins repeated!"
            )
            print(alert_text, flush=True)
            await send_bot_notification(alert_text)
        else:
            alert_text = f"[{chat_title}] - New Signal Alert at {formatted_time} | Time gap: {current_gap} mins"
            print(alert_text, flush=True)
            await send_bot_notification(alert_text)

        # Update tracking history for this channel
        channel_history[chat_id] = {
            "last_time": current_time,
            "last_gap": current_gap,
        }
    else:
        # First matching message seen in this channel
        channel_history[chat_id] = {"last_time": current_time, "last_gap": None}
        init_text = f"[{chat_title}] - First Signal Recorded at {formatted_time} | Tracking initiated."
        print(init_text, flush=True)
        await send_bot_notification(init_text)


async def main():
    print("Userbot started and listening to channels...", flush=True)
    await client.start()
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
