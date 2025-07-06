import os
import requests
from tqdm import tqdm
from pixeldrain_reloaded import Sync
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

user_keys = {}  # Store API keys per user

def download_with_progress(url, output_path):
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    with open(output_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True) as pbar:
        for chunk in resp.iter_content(8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

def upload_file(filepath, api_key):
    return Sync.upload_file(
        path=filepath,
        returns="verbose_dict",
        filename=os.path.basename(filepath),
        api_key=api_key
    )

def start(update, context):
    update.message.reply_text(
        "👋 Welcome to PixelUploader Bot!\n\n"
        "Send /key <your_pixeldrain_api_key> to set your API key.\n"
        "Then send /send <video_url> to upload a video."
    )

def set_key(update, context):
    user_id = update.message.from_user.id
    if len(context.args) != 1:
        update.message.reply_text("❌ Usage: /key <your_pixeldrain_api_key>")
        return
    user_keys[user_id] = context.args[0]
    update.message.reply_text("✅ API key set! Now use /send <url> to upload.")

def send_video(update, context):
    user_id = update.message.from_user.id
    if user_id not in user_keys:
        update.message.reply_text("❌ Please set your API key first using /key <your_api_key>")
        return

    if not context.args:
        update.message.reply_text("❌ Usage: /send <video_url>")
        return

    url = context.args[0]
    filename = url.split("/")[-1] or "video.mp4"
    update.message.reply_text("⬇️ Downloading...")

    try:
        download_with_progress(url, filename)
    except Exception as e:
        update.message.reply_text(f"❌ Download failed: {e}")
        return

    update.message.reply_text("⬆️ Uploading to Pixeldrain...")

    try:
        result = upload_file(filename, user_keys[user_id])
        file_id = result.get("id")
        os.remove(filename)

        if file_id:
            pixeldrain_url = f"https://pixeldrain.com/u/{file_id}"
            update.message.reply_text(f"✅ Uploaded!\n🔗 {pixeldrain_url}")
        else:
            update.message.reply_text("❌ Upload failed, no file ID returned.")
    except Exception as e:
        update.message.reply_text(f"❌ Upload failed: {e}")

def unknown(update, context):
    update.message.reply_text("❓ Unknown command.")

def main():
    TELEGRAM_TOKEN = os.getenv("8118249527:AAHcGtzsAsC6_gA5_0vyeY5rw1rFAMgDLV8")  # 🔒 Loaded from environment
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("key", set_key))
    dp.add_handler(CommandHandler("send", send_video))
    dp.add_handler(MessageHandler(Filters.command, unknown))

    print("🤖 Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
