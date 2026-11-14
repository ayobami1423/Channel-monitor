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

# Exact loss message template to watch for
LOSS_MESSAGE = """❌ LOSS

😔 Not this time...
💪 Wait for the next signal!
🎯 Patience and discipline win."""

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
    print("Connecting to Telegram to scan for recent losses...", flush=True)
    await client.start()
    
    await send_telegram_message("🔍 **Scanning channels for recent loss messages and extracting their 10-message histories...** Please wait.")

    found_any = False

    for channel_id in CHANNELS:
        try:
            entity = await client.get_entity(channel_id)
            chat_title = getattr(entity, "title", str(channel_id))

            # Scan the last 50 messages in the channel to find recent loss messages
            async for message in client.iter_messages(entity, limit=50):
                msg_text = message.raw_text.strip() if message.raw_text else ""
                
                if LOSS_MESSAGE.strip() in msg_text:
                    found_any = True
                    
                    # Generate link for the loss message
                    if entity.username:
                        loss_link = f"https://t.me/{entity.username}/{message.id}"
                    else:
                        clean_id = str(entity.id).replace("-100", "")
                        loss_link = f"https://t.me/c/{clean_id}/{message.id}"

                    # Fetch the 10 messages leading up to this loss message (newest to oldest)
                    history_lines = []
                    async for prev_msg in client.iter_messages(entity, limit=10, max_id=message.id):
                        prev_text = prev_msg.raw_text.strip() if prev_msg.raw_text else "[Media / Non-text Message]"
                        if len(prev_text) > 70:
                            prev_text = prev_text[:70] + "..."

                        if entity.username:
                            prev_link = f"https://t.me/{entity.username}/{prev_msg.id}"
                        else:
                            clean_id = str(entity.id).replace("-100", "")
                            prev_link = f"https://t.me/c/{clean_id}/{prev_msg.id}"

                        history_lines.append(f"🔗 {prev_link}\n💬 {prev_text}")

                    history_text = "\n\n".join(history_lines) if history_lines else "No previous history found."

                    # Compile report for this loss event
                    report = (
                        f"🚨 RECENT LOSS FOUND 🚨\n"
                        f"Channel: {chat_title}\n"
                        f"🔗 Loss Message Link: {loss_link}\n\n"
                        f"📋 PREVIOUS 10 MESSAGES (Newest to Oldest):\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"{history_text}"
                    )

                    await send_telegram_message(report)
                    await asyncio.sleep(1)
                    
                    # Optional: limit to the most recent loss per channel so it doesn't spam too many old ones
                    break 

        except Exception as e:
            print(f"Could not scan channel {channel_id}: {e}", flush=True)

    if not found_any:
        await send_telegram_message("ℹ️ No recent loss messages were found in the scanned history of your channels.")

    await send_telegram_message("✅ **History scan complete!**")
    print("Scan complete!", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
