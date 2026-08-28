import os
import logging
import sqlite3
import secrets

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["BOT_TOKEN"]

DB_FILE = "movies.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            file_id TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if context.args:
        code = context.args[0]

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT file_id FROM movies WHERE code = ?",
            (code,)
        )

        result = cursor.fetchone()
        conn.close()

        if not result:
            await update.message.reply_text(
                "❌ Movie not found."
            )
            return

        file_id = result[0]

        sent_message = await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=file_id,
            caption="🎬 Enjoy the movie."
        )

        context.job_queue.run_once(
            delete_movie_message,
            600,
            data={
                "chat_id": update.effective_chat.id,
                "message_id": sent_message.message_id,
            },
        )

        await update.message.reply_text(
            "⏳ This movie will disappear in 10 minutes."
        )

        return

    await update.message.reply_text(
        "🎬 Send a movie link to get started."
    )


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Your Telegram ID:\n{update.effective_user.id}"
    )


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏳ Send me your Telegram ID first with /id."
    )


async def delete_movie_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job

    try:
        await context.bot.delete_message(
            chat_id=job.data["chat_id"],
            message_id=job.data["message_id"],
        )

    except Exception as e:
        logging.warning(f"Delete failed: {e}")


def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))

    app.add_handler(
        MessageHandler(filters.VIDEO, receive_video)
    )

    print("LemochBot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
