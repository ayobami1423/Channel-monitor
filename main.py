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

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


async def send_bot_notification(text: str):
    """Sends the formatted alert to your private chat via your Telegram Bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    async with httpx.AsyncClient() as http_client:
        try:
            await http_client.post(url, json=payload)
        except Exception as e:
            print(f"Failed to send bot notification: {e}", flush=True)


@client.on(events.NewMessage(chats=CHANNELS))
async def handle_message(event):
    message_text = event.raw_text.strip()

    # Check if the message is a win notification
    is_mega_win = "🚀 MEGA WIN!" in message_text
    is_normal_win = "🎉 YOU WON!" in message_text

    if not (is_mega_win or is_normal_win):
        return

    # Strictly verify that it is Martingale 4 or Martingale 5
    if (
        "(WIN (MARTINGALE 4))" not in message_text
        and "(WIN (MARTINGALE 5))" not in message_text
    ):
        return

    chat = await event.get_chat()
    chat_title = getattr(chat, "title", str(chat.id))

    current_time = datetime.now()
    formatted_time = current_time.strftime("%I:%M %p")  # 12-hour format AM/PM

    # Generate the direct link to the message if the channel has a username or public/private structure
    message_link = None
    if chat.username:
        message_link = f"https://t.me/{chat.username}/{event.id}"
    else:
        # For supergroups/channels with IDs like -100xxxxxxxxxx, format the link cleanly
        clean_id = str(chat.id).replace("-100", "")
        message_link = f"https://t.me/c/{clean_id}/{event.id}"

    # Construct the alert to send to your private chat with the link included
    alert_text = (
        f"🚨 TARGET MARTINGALE HIT! 🚨\n"
        f"Channel: {chat_title}\n"
        f"Time: {formatted_time}\n"
        f"🔗 Message Link: {message_link}\n\n"
        f"{message_text}"
    )

    print(alert_text, flush=True)
    await send_bot_notification(alert_text)


async def main():
    print(
        "Userbot started and listening for Martingale 4 & 5 wins...",
        flush=True,
    )
    await client.start()
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
