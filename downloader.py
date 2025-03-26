import os
import re
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from telethon import TelegramClient
from telethon.errors import FloodWaitError, RPCError

# --------- Setup Logging ---------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --------- Load Config ---------
CONFIG = {
    "api_id": "26973577",       # Your Telegram API ID
    "api_hash": "bf3596c4fbf3689f2df5d6c2c2428a4a",     # Your Telegram API Hash
    "channel": "RadioRockie",  # Target channel username
    "download_path": "downloaded_music",
    "session_file": "my_session",
    "max_retries": 3,   # Retry failed downloads
    "delay_between_downloads": 2  # Avoid rate limits (seconds)
}

# --------- Helper Functions ---------
def clean_filename(filename: str) -> str:
    """Remove invalid characters from filenames."""
    return re.sub(r'[<>:"/\\|?*]', '', filename).strip()

async def is_valid_mp3(file_path: str) -> bool:
    """Check if file is a valid MP3 by reading its header."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(3)
            return header == b'ID3'  # MP3 files start with 'ID3'
    except Exception:
        return False

# --------- Main Downloader ---------
async def download_music(client: TelegramClient):
    Path(CONFIG["download_path"]).mkdir(exist_ok=True)
    downloaded_files = set(os.listdir(CONFIG["download_path"]))
    report = []

    try:
        async for msg in client.iter_messages(CONFIG["channel"]):
            if not (msg.file and msg.file.mime_type and 'audio' in msg.file.mime_type):
                continue

            filename = clean_filename(msg.file.name or f"{msg.id}.mp3")
            filepath = os.path.join(CONFIG["download_path"], filename)

            if filename in downloaded_files:
                logger.info(f"⏩ Already exists: {filename}")
                continue

            for attempt in range(CONFIG["max_retries"]):
                try:
                    logger.info(f"⬇️ Downloading ({attempt + 1}/{CONFIG['max_retries']}): {filename}")
                    await msg.download_media(file=filepath)
                    
                    if await is_valid_mp3(filepath):
                        report.append({
                            "file_name": filename,
                            "size": f"{msg.file.size / (1024 * 1024):.2f} MB",
                            "date": datetime.now().isoformat()
                        })
                        logger.info(f"✅ Success: {filename}")
                        break
                    else:
                        os.remove(filepath)
                        logger.error(f"❌ Invalid MP3: {filename}")

                except FloodWaitError as e:
                    logger.warning(f"⏳ Flood wait: {e.seconds} seconds")
                    await asyncio.sleep(e.seconds)
                except RPCError as e:
                    logger.error(f"⚠️ Telegram error: {e}")
                    await asyncio.sleep(CONFIG["delay_between_downloads"])
                except Exception as e:
                    logger.error(f"❌ Failed: {filename} - {str(e)}")
                    await asyncio.sleep(CONFIG["delay_between_downloads"])

    finally:
        with open("download_report.json", "w") as f:
            json.dump(report, f, indent=4)
        logger.info("📝 Download report saved.")

# --------- Entry Point ---------
async def main():
    client = TelegramClient(
        session=CONFIG["session_file"],
        api_id=CONFIG["api_id"],
        api_hash=CONFIG["api_hash"]
    )
    await client.start()
    await download_music(client)
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())