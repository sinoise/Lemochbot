import os
import logging
import asyncio

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Send me a movie to get started."
    )


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Movie received."
    )


async def delete_after_10_minutes(
    context: ContextTypes.DEFAULT_TYPE
):
    job = context.job
    chat_id = job.data["chat_id"]
    message_id = job.data["message_id"]

    try:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )
    except Exception as e:
        logging.warning(f"Could not delete message: {e}")


async def send_movie(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    # This will be connected to the movie database later.
    await update.message.reply_text(
        "🎬 Your movie will appear here."
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(filters.VIDEO, receive_video)
    )

    app.add_handler(
        CommandHandler("movie", send_movie)
    )

    print("LemochBot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
