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

from groq import Groq


# =========================
# ENVIRONMENT VARIABLES
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing!")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing!")


# =========================
# GROQ CLIENT
# =========================

groq_client = Groq(api_key=GROQ_API_KEY)

MODEL = "llama-3.3-70b-versatile"


# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 আমি এখন Groq AI-এর সাথে connected!\n\n"
        "আপনি আমাকে যেকোনো প্রশ্ন করতে পারেন।"
    )


# =========================
# AI HANDLER
# =========================

async def ai_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message or not update.message.text:
        return

    user_message = update.message.text

    await update.message.chat.send_action("typing")

    try:

        response = await asyncio.to_thread(
            groq_client.chat.completions.create,
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful AI assistant. "
                        "Answer clearly and accurately. "
                        "If the user speaks Bengali, reply in Bengali."
                    ),
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        ai_reply = response.choices[0].message.content

        if not ai_reply:
            ai_reply = "দুঃখিত, কোনো উত্তর পাওয়া যায়নি।"

        # Telegram message length handling
        max_length = 4000

        for i in range(0, len(ai_reply), max_length):

            await update.message.reply_text(
                ai_reply[i:i + max_length]
            )

    except Exception as e:

        logger.error("Groq API Error: %s", e)

        await update.message.reply_text(
            "❌ AI-এর সাথে যোগাযোগ করতে সমস্যা হয়েছে।\n\n"
            f"Error: {str(e)[:500]}"
        )


# =========================
# MAIN
# =========================

def main():

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            ai_message
        )
    )

    print("🤖 Groq AI Telegram Bot is running...")

    app.run_polling()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
