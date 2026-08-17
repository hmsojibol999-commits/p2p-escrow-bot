import os
import telebot
from telebot import types

# Token will come from Render Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)


# =========================
# HOME
# =========================

def home_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(
        types.InlineKeyboardButton(
            "🔎 Find a Service",
            callback_data="find"
        )
    )

    kb.add(
        types.InlineKeyboardButton("🤖 AI", callback_data="cat_ai"),
        types.InlineKeyboardButton("🌐 Web", callback_data="cat_web"),
    )

    kb.add(
        types.InlineKeyboardButton("🤖 Telegram Bots", callback_data="cat_bot"),
        types.InlineKeyboardButton("📱 Apps", callback_data="cat_apps"),
    )

    kb.add(
        types.InlineKeyboardButton("💻 Software", callback_data="cat_software"),
        types.InlineKeyboardButton("🎨 Design", callback_data="cat_design"),
    )

    kb.add(
        types.InlineKeyboardButton("🔥 Popular", callback_data="popular"),
        types.InlineKeyboardButton("✨ Recommended", callback_data="recommended"),
    )

    kb.add(
        types.InlineKeyboardButton("❤️ Saved", callback_data="saved"),
        types.InlineKeyboardButton("👤 Profile", callback_data="profile"),
    )

    return kb


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    text = """
🤖 *SMART HUB*

_Your Digital Solution Hub_

━━━━━━━━━━━━━━━━━━

Useful digital services, tools,
AI platforms, Telegram bots,
apps and software — all in one place.

👇 What are you looking for?
"""

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=home_keyboard()
    )


# =========================
# FIND SERVICE
# =========================

@bot.callback_query_handler(func=lambda c: c.data == "find")
def find_service(call):

    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(
        types.InlineKeyboardButton(
            "🤖 Telegram Bot",
            callback_data="type_bot"
        ),
        types.InlineKeyboardButton(
            "🌐 Web Platform",
            callback_data="type_web"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "📱 Mobile App",
            callback_data="type_app"
        ),
        types.InlineKeyboardButton(
            "💻 Software",
            callback_data="type_software"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🧩 Browser Extension",
            callback_data="type_extension"
        ),
        types.InlineKeyboardButton(
            "🔌 API / Developer Tool",
            callback_data="type_api"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Home",
            callback_data="home"
        )
    )

    bot.edit_message_text(
        """
🔎 *FIND A SERVICE*

প্রথমে service-এর ধরন নির্বাচন করুন।
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================
# CATEGORY
# =========================

@bot.callback_query_handler(func=lambda c: c.data.startswith("type_"))
def choose_category(call):

    kb = types.InlineKeyboardMarkup(row_width=2)

    categories = [
        ("🤖 AI", "filter_ai"),
        ("🎨 Design", "filter_design"),
        ("👨‍💻 Developer", "filter_dev"),
        ("📚 Education", "filter_edu"),
        ("💼 Business", "filter_business"),
        ("⚡ Productivity", "filter_productivity"),
        ("☁️ Cloud", "filter_cloud"),
        ("🔐 Security", "filter_security"),
    ]

    for name, data in categories:
        kb.add(types.InlineKeyboardButton(name, callback_data=data))

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Back",
            callback_data="find"
        )
    )

    bot.edit_message_text(
        """
🗂️ *SELECT CATEGORY*

আপনার প্রয়োজনীয় category নির্বাচন করুন।
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================
# FILTERS
# =========================

@bot.callback_query_handler(func=lambda c: c.data.startswith("filter_"))
def filters(call):

    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(
        types.InlineKeyboardButton(
            "🆓 Free",
            callback_data="free"
        ),
        types.InlineKeyboardButton(
            "💎 Premium",
            callback_data="premium"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⭐ 4.5+ Rating",
            callback_data="rating"
        ),
        types.InlineKeyboardButton(
            "🛡️ Verified",
            callback_data="verified"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🔥 Popular",
            callback_data="popular_filter"
        ),
        types.InlineKeyboardButton(
            "🆕 New",
            callback_data="new"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🔍 SHOW RESULTS",
            callback_data="results"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Home",
            callback_data="home"
        )
    )

    bot.edit_message_text(
        """
⚙️ *FILTERS*

আপনার প্রয়োজন অনুযায়ী filter নির্বাচন করুন।
একাধিক filter ব্যবহার করা যাবে।
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================
# RESULTS
# =========================

@bot.callback_query_handler(func=lambda c: c.data == "results")
def results(call):

    kb = types.InlineKeyboardMarkup(row_width=1)

    kb.add(
        types.InlineKeyboardButton(
            "🤖 AI Image Tool ⭐ 4.9 🛡️",
            callback_data="service_1"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🎨 Creative AI ⭐ 4.8 🛡️",
            callback_data="service_2"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "✨ Image Generator ⭐ 4.7",
            callback_data="service_3"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Back",
            callback_data="find"
        )
    )

    bot.edit_message_text(
        """
🎯 *MATCHING SERVICES*

আপনার নির্বাচিত filters অনুযায়ী
এই services পাওয়া গেছে।
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================
# SERVICE DETAILS
# =========================

@bot.callback_query_handler(func=lambda c: c.data.startswith("service_"))
def service_details(call):

    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(
        types.InlineKeyboardButton(
            "🚀 Open Service",
            url="https://example.com"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "❤️ Save",
            callback_data="saved"
        ),
        types.InlineKeyboardButton(
            "⚖️ Compare",
            callback_data="compare"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Back",
            callback_data="results"
        )
    )

    bot.edit_message_text(
        """
🤖 *AI IMAGE TOOL*

🛡️ Verified
⭐ Rating: 4.9
📊 Trust Score: 94/100

━━━━━━━━━━━━━━━━━━

📝 *About*

AI দিয়ে image তৈরি করার
জন্য একটি useful digital service।

✨ *Features*

✅ Image Generation
✅ Easy Interface
✅ Free Plan
✅ Fast Processing

💰 *Pricing*

🆓 Free Plan Available

📅 Last Verified:
August 2026
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================
# HOME CALLBACK
# =========================

@bot.callback_query_handler(func=lambda c: c.data == "home")
def go_home(call):

    bot.edit_message_text(
        """
🤖 *SMART HUB*

_Your Digital Solution Hub_

━━━━━━━━━━━━━━━━━━

Useful digital services, tools,
AI platforms, Telegram bots,
apps and software — all in one place.

👇 What are you looking for?
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=home_keyboard()
    )


# =========================
# OTHER SECTIONS
# =========================

@bot.callback_query_handler(
    func=lambda c: c.data in [
        "popular",
        "recommended",
        "saved",
        "profile",
        "compare"
    ]
)
def other_sections(call):

    titles = {
        "popular": "🔥 POPULAR",
        "recommended": "✨ RECOMMENDED",
        "saved": "❤️ SAVED",
        "profile": "👤 PROFILE",
        "compare": "⚖️ COMPARE"
    }

    title = titles.get(call.data, "SMART HUB")

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Home",
            callback_data="home"
        )
    )

    bot.edit_message_text(
        f"*{title}*\n\nএই section-এর বিস্তারিত feature পরে তৈরি করা হবে।",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================
# START BOT
# =========================

print("🤖 Smart Hub Bot is running...")

bot.infinity_polling(skip_pending=True)
