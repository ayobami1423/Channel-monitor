import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import httpx

# --- CONFIGURATION & CREDENTIALS ---
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


async def send_telegram_message(text: str):
    """Sends a message to your private Telegram chat via your bot"""
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
            print(f"Failed to send telegram notification: {e}", flush=True)


async def main():
    print("Connecting to Telegram to fetch all 100 messages...", flush=True)
    await client.start()
    
    await send_telegram_message("🔍 **Starting history extraction:** Fetching the last 10 messages for all 10 channels (100 messages total)... Please wait.")

    for channel_id in CHANNELS:
        try:
            entity = await client.get_entity(channel_id)
            chat_title = getattr(entity, "title", str(channel_id))
            
            history_lines = [f"📊 **CHANNEL: {chat_title}**\n*(Last 10 Messages)*\n━━━━━━━━━━━━━━━━━━━━"]
            count = 0

            # Fetch last 10 messages from newest to oldest for this specific channel
            async for message in client.iter_messages(entity, limit=10):
                count += 1
                msg_text = message.raw_text.strip() if message.raw_text else "[Media / Non-text Message]"
                if len(msg_text) > 70:
                    msg_text = msg_text[:70] + "..."

                if entity.username:
                    msg_link = f"https://t.me/{entity.username}/{message.id}"
                else:
                    clean_id = str(entity.id).replace("-100", "")
                    msg_link = f"https://t.me/c/{clean_id}/{message.id}"

                history_lines.append(f"{count}. 🔗 {msg_link}\n   💬 {msg_text}")

            # Send this channel's 10 messages as a dedicated report block
            channel_report = "\n\n".join(history_lines)
            await send_telegram_message(channel_report)
            
            # Short pause between channels to avoid Telegram rate limits
            await asyncio.sleep(1.5)

        except Exception as e:
            error_msg = f"❌ Could not fetch history for channel `{channel_id}`: {e}"
            await send_telegram_message(error_msg)

    await send_telegram_message("✅ **All 100 messages fetched and sent successfully!**")
    print("All 100 messages sent to Telegram!", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
