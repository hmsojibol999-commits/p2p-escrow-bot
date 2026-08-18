import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Environment variables থেকে Key পড়া
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq client ইনিশিয়ালাইজ করা
groq_client = Groq(api_key=GROQ_API_KEY)

# /start কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হ্যালো! আমি Groq AI দ্বারা চালিত একটি বট। আমাকে যেকোনো প্রশ্ন করতে পারেন।")

# মেসেজ প্রসেসিং ও Groq Response তৈরি
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # টাইপিং ইন্ডিকেটর দেখানো
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Groq API-তে রিকোয়েস্ট পাঠানো (Llama 3 মডেল ব্যবহার করা হয়েছে)
        response = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"দুঃখিত, কোনো সমস্যা হয়েছে: {str(e)}")

if __name__ == '__main__':
    if not BOT_TOKEN or not GROQ_API_KEY:
        print("Error: BOT_TOKEN or GROQ_API_KEY environment variable missing!")
        exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is running...")
    app.run_polling()
    
