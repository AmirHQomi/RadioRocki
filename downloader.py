import os
import re
import asyncio
import json
from telethon import TelegramClient

# --------- تنظیمات API تلگرام ---------
api_id = '26973577'  # باید از تلگرام API ID خود استفاده کنید
api_hash = 'bf3596c4fbf3689f2df5d6c2c2428a4a'  # باید از تلگرام API Hash خود استفاده کنید
channel_username = 'RadioRockie'  # نام کانال تلگرام

# مسیر ذخیره فایل‌ها
save_path = 'downloaded_music'
os.makedirs(save_path, exist_ok=True)

# مسیر ذخیره سشن تلگرام
session_name = 'my_session'

# --------- توابع کمکی ---------
# تابع پاکسازی نام فایل
def clean_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

# تابع دانلود فایل از تلگرام
async def download_music(client):
    downloaded_files = set(os.listdir(save_path))  # فایل‌هایی که قبلاً دانلود شده‌اند را بشناسیم
    report = []

    # وارد شدن به کانال و بررسی پیام‌ها
    async for msg in client.iter_messages(channel_username):
        if msg.file and msg.file.mime_type and 'audio' in msg.file.mime_type:
            # بررسی اینکه آیا فایل قبلاً دانلود شده است یا نه
            file_name = clean_filename(msg.file.name or f'{msg.id}.mp3')
            full_path = os.path.join(save_path, file_name)

            # اگر فایل قبلاً دانلود شده باشد، از دانلود دوباره آن خودداری می‌کنیم
            if file_name in downloaded_files:
                print(f'⚡ {file_name} already downloaded, skipping...')
                continue

            print(f'Downloading: {file_name}')
            try:
                # دانلود فایل از تلگرام
                await msg.download_media(file=full_path)
                downloaded_files.add(file_name)

                # ثبت نام فایل در گزارش
                report.append({
                    'file_name': file_name,
                    'download_path': full_path
                })
                print(f'✔ {file_name} downloaded successfully.')

            except Exception as e:
                print(f'❌ Failed to download {file_name}: {e}')

    # ذخیره گزارش دانلودها در فایل JSON
    with open('download_report.json', 'w') as f:
        json.dump(report, f, indent=4)
    print('✅ All files downloaded successfully.')

# --------- اجرای کد دانلود ---------
async def main():
    async with TelegramClient(session_name, api_id, api_hash) as client:
        await download_music(client)

# اجرای اصلی برنامه
if __name__ == "__main__":
    asyncio.run(main())
