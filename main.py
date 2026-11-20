import asyncio
from datetime import datetime
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
    -1004429
