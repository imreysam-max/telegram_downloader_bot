import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋\nلینک یوتوب، اینستاگرام، اپارات یا ساندکلاود رو بفرست تا دانلودش کنم! 🎬🎵"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return
    context.user_data["url"] = url
    keyboard = [
        [InlineKeyboardButton("🎬 ویدیو - کیفیت بالا", callback_data="video_best")],
        [InlineKeyboardButton("🎬 ویدیو - کیفیت متوسط", callback_data="video_medium")],
        [InlineKeyboardButton("🎵 فقط صدا (MP3)", callback_data="audio")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("چه فرمتی می‌خوای؟", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get("url")
    if not url:
        await query.edit_message_text("لینک پیدا نشد، دوباره بفرست.")
        return
    await query.edit_message_text("⏳ در حال دانلود...")
    choice = query.data
    try:
        if choice == "audio":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "/tmp/%(title)s.%(ext)s",
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
            }
        elif choice == "video_medium":
            ydl_opts = {
                "format": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                "outtmpl": "/tmp/%(title)s.%(ext)s",
                "merge_output_format": "mp4",
            }
        else:
            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "outtmpl": "/tmp/%(title)s.%(ext)s",
                "merge_output_format": "mp4",
            }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if choice == "audio":
                filename = filename.rsplit(".", 1)[0] + ".mp3"
        with open(filename, "rb") as f:
            if choice == "audio":
                await query.message.reply_audio(f)
            else:
                await query.message.reply_video(f)
        os.remove(filename)
    except Exception as e:
        await query.message.reply_text(f"❌ خطا: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
