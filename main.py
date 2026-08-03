import os
import threading
import pyotp
from flask import Flask
from telethon import TelegramClient, events
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- রেন্ডারের পোর্ট ওপেন রাখার জন্য ফ্লাস্ক সার্ভার ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Smart Account Supply Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# --- কনফিগারেশন ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "your_api_hash_here")
SESSION_NAME = "my_userbot"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "your_bot_token_here")

OTP_SOURCES = [] 
FA_SECRETS = {}  
DAILY_COUNT = 0  

# টেলিগ্রাম ইউজারবট (অটো-ফরওয়ার্ডিংয়ের জন্য)
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.NewMessage)
async def handle_incoming_message(event):
    if OTP_SOURCES:
        sender = await event.get_sender()
        sender_username = getattr(sender, 'username', None)
        sender_id = str(sender.id)
        
        if (sender_username and sender_username in OTP_SOURCES) or (sender_id in OTP_SOURCES):
            print(f"🔔 নতুন ওটিপি পাওয়া গেছে: {event.raw_text}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 ওটিপি বট লিস্ট", callback_data="list_bots")],
        [InlineKeyboardButton("🔑 2FA কোড জেনারেট", callback_data="list_2fa")],
        [InlineKeyboardButton("📊 আজকের কাজের হিসাব", callback_data="stats")],
        [InlineKeyboardButton("➕ বট বা সিক্রেট যোগ করুন", callback_data="help_add")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🚀 **অ্যাকাউন্ট সাপ্লাই স্মার্ট প্যানেলে স্বাগতম!**\nনিচের অপশন থেকে আপনার প্রয়োজনীয় কাজ সিলেক্ট করুন:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "list_bots":
        if not OTP_SOURCES:
            await query.edit_message_text("📭 কোনো ওটিপি সোর্স নেই। যোগ করতে `/add_bot @username` লিখুন।")
        else:
            bots_list = "\n".join([f"• {b}" for b in OTP_SOURCES])
            await query.edit_message_text(f"📋 **সেভ করা সোর্সসমূহ:**\n\n{bots_list}")
            
    elif query.data == "list_2fa":
        if not FA_SECRETS:
            await query.edit_message_text("📭 কোনো 2FA সিক্রেট কি সেভ করা নেই। যোগ করতে `/add_2fa [নাম] [সিক্রেট_কি]` লিখুন।")
        else:
            fa_list = "\n".join([f"• **{name}**: `{pyotp.TOTP(key).now()}`" for name, key in FA_SECRETS.items()])
            await query.edit_message_text(f"🔑 **বর্তমান 2FA কোডসমূহ (ক্লিক করে কপি করুন):**\n\n{fa_list}")
            
    elif query.data == "stats":
        global DAILY_COUNT
        await query.edit_message_text(f"📊 আজ মোট সফল অ্যাকাউন্ট তৈরি হয়েছে: **{DAILY_COUNT} টি**\n\nবাড়াতে `/add_count` কমান্ড দিন।")
        
    elif query.data == "help_add":
        await query.edit_message_text("💡 **কমান্ড গাইড:**\n1. বট যোগ করতে: `/add_bot @username`\n2. 2FA কি যোগ করতে: `/add_2fa AccName SecretKey`\n3. একাউন্ট কাউন্ট বাড়াতে: `/add_count`")

async def add_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        source = context.args[0]
        if source not in OTP_SOURCES:
            OTP_SOURCES.append(source)
            await update.message.reply_text(f"✅ সফলভাবে বট যোগ করা হয়েছে: {source}")
        else:
            await update.message.reply_text("⚠️ এটি আগেই লিস্টে আছে!")
    else:
        await update.message.reply_text("ব্যবহারবিধি: `/add_bot @bot_username`")

async def add_2fa(update: Update, context: Context_DEFAULT_TYPE = None):
    # (Fix for context argument compatibility)
    pass

async def add_2fa_real(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) >= 2:
        name = context.args[0]
        secret_key = context.args[1]
        try:
            pyotp.TOTP(secret_key).now()
            FA_SECRETS[name] = secret_key
            await update.message.reply_text(f"✅ সাকসেসফুল! **{name}** এর 2FA সিক্রেট সেভ হয়েছে।")
        except Exception:
            await update.message.reply_text("❌ ভুল সিক্রেট কি! সঠিক বেস৩২ কি দিন।")
    else:
        await update.message.reply_text("ব্যবহারবিধি: `/add_2fa [নাম] [সিক্রেট_কি]`")

async def add_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DAILY_COUNT
    DAILY_COUNT += 1
    await update.message.reply_text(f"📈 কাউন্ট ১ বাড়লো! আজকের মোট অ্যাকাউন্ট: **{DAILY_COUNT} টি**")

def main():
    # ফ্লাস্ক সার্ভার আলাদা থ্রেডে রান করানো যাতে রেন্ডার পোর্ট ওপেন পায়
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("add_bot", add_bot))
    app.add_handler(CommandHandler("add_2fa", add_2fa_real))
    app.add_handler(CommandHandler("add_count", add_count))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 স্মার্ট সাপ্লাই বট এবং ওয়েব সার্ভার চালু হয়েছে...")
    client.start()
    app.run_polling()

if __name__ == "__main__":
    main()
    
