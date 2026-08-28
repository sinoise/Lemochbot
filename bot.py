import os
import sqlite3
import secrets
import logging

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

ADMIN_ID = 379290695

DB_FILE = "movies.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            file_id TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "🎬 Send a movie link to watch."
        )
        return

    code = context.args[0]

    conn = sqlite3.connect(DB_FILE)

    result = conn.execute(
        "SELECT file_id FROM movies WHERE code = ?",
        (code,)
    ).fetchone()

    conn.close()

    if not result:
        await update.message.reply_text(
            "❌ Movie not found."
        )
        return

    file_id = result[0]

    movie_message = await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=file_id,
        caption="🎬 Enjoy."
    )

    context.job_queue.run_once(
        delete_movie,
        600,
        data={
            "chat_id": update.effective_chat.id,
            "message_id": movie_message.message_id,
        }
    )

    await update.message.reply_text(
        "⏳ This message disappears in 10 minutes."
    )


async def receive_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "Sorry, only the bot owner can add movies."
        )
        return

    video = update.message.video

    code = secrets.token_urlsafe(6)

    conn = sqlite3.connect(DB_FILE)

    conn.execute(
        "INSERT INTO movies (code, file_id) VALUES (?, ?)",
        (code, video.file_id)
    )

    conn.commit()
    conn.close()

    bot_username = (await context.bot.get_me()).username

    link = f"https://t.me/{bot_username}?start={code}"

    await update.message.reply_text(
        f"✅ Movie saved.\n\n"
        f"🔗 Link:\n{link}"
    )


async def delete_movie(context: ContextTypes.DEFAULT_TYPE):

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

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.VIDEO,
            receive_video
        )
    )

    print("LemochBot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
