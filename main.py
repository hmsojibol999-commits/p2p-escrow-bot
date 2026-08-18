import os
import telebot
from telebot import types

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing.")

bot = telebot.TeleBot(BOT_TOKEN)


# =========================================================
# DEMO APP DATA
# Later this will come from Database
# =========================================================

APPS = [
    {
        "id": 1,
        "name": "Business App One",
        "category": "business",
        "rating": "4.8",
        "pricing": "🟡 Freemium",
        "description": "Business management and productivity app.",
        "features": "Customer management • Reports • Productivity",
        "bot_file": True,
        "website": "https://example.com",
        "playstore": "https://play.google.com/",
    },
    {
        "id": 2,
        "name": "Business App Two",
        "category": "business",
        "rating": "4.7",
        "pricing": "🟢 Free",
        "description": "Useful tools for small businesses.",
        "features": "Planning • Tracking • Business tools",
        "bot_file": False,
        "website": "https://example.com",
        "playstore": "https://play.google.com/",
    },
    {
        "id": 3,
        "name": "Business App Three",
        "category": "business",
        "rating": "4.6",
        "pricing": "🔵 Paid",
        "description": "Professional business management application.",
        "features": "Advanced tools • Analytics • Management",
        "bot_file": False,
        "website": "https://example.com",
        "playstore": "https://play.google.com/",
    },

    {
        "id": 4,
        "name": "Business App Four",
        "category": "business",
        "rating": "4.5",
        "pricing": "🟣 Trial",
        "description": "Business planning and organization tool.",
        "features": "Planning • Tasks • Organization",
        "bot_file": False,
        "website": "https://example.com",
        "playstore": "https://play.google.com/",
    },
    {
        "id": 5,
        "name": "Business App Five",
        "category": "business",
        "rating": "4.4",
        "pricing": "🟡 Freemium",
        "description": "Simple business utility application.",
        "features": "Management • Tracking • Reports",
        "bot_file": False,
        "website": "https://example.com",
        "playstore": "https://play.google.com/",
    },
    {
        "id": 6,
        "name": "Business App Six",
        "category": "business",
        "rating": "4.3",
        "pricing": "🟢 Free",
        "description": "Free tools for everyday business work.",
        "features": "Tasks • Notes • Organization",
        "bot_file": False,
        "website": "https://example.com",
        "playstore": "https://play.google.com/",
    },
]


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():

    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(
        types.InlineKeyboardButton(
            "🤖 Telegram Bots",
            callback_data="bots"
        ),
        types.InlineKeyboardButton(
            "📱 Apps",
            callback_data="apps"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "💻 Software",
            callback_data="software"
        ),
        types.InlineKeyboardButton(
            "🌐 Web Platforms",
            callback_data="web"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🤖 AI Tools",
            callback_data="ai"
        )
    )

    return kb


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    text = """
🤖 *SMART HUB*

আপনার প্রয়োজনীয় digital service
সহজে খুঁজে নিন।

নিচের একটি option নির্বাচন করুন।
"""

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# =========================================================
# APPS CATEGORY
# =========================================================

@bot.callback_query_handler(func=lambda c: c.data == "apps")
def apps_menu(call):

    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(
        types.InlineKeyboardButton(
            "🤖 AI",
            callback_data="appcat_ai"
        ),
        types.InlineKeyboardButton(
            "🎨 Design",
            callback_data="appcat_design"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "💼 Business",
            callback_data="appcat_business"
        ),
        types.InlineKeyboardButton(
            "📚 Education",
            callback_data="appcat_education"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🎮 Gaming",
            callback_data="appcat_gaming"
        ),
        types.InlineKeyboardButton(
            "🛠️ Utility",
            callback_data="appcat_utility"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Back",
            callback_data="home"
        )
    )

    bot.edit_message_text(
        """
📱 *APPS*

আপনার প্রয়োজন অনুযায়ী category নির্বাচন করুন।
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================================================
# APP LIST
# =========================================================

APPS_PER_PAGE = 3


def get_category_apps(category):

    return [
        app for app in APPS
        if app["category"] == category
    ]


def app_list_keyboard(category, page):

    apps = get_category_apps(category)

    start = page * APPS_PER_PAGE
    page_apps = apps[start:start + APPS_PER_PAGE]

    kb = types.InlineKeyboardMarkup(row_width=1)

    for app in page_apps:

        kb.add(
            types.InlineKeyboardButton(
                f'{app["id"]}. {app["name"]}  ⭐{app["rating"]}',
                callback_data=f'app_{app["id"]}'
            )
        )

    navigation = []

    if page > 0:
        navigation.append(
            types.InlineKeyboardButton(
                "◀️ Previous",
                callback_data=f"page_{category}_{page-1}"
            )
        )

    if start + APPS_PER_PAGE < len(apps):
        navigation.append(
            types.InlineKeyboardButton(
                "Next ▶️",
                callback_data=f"page_{category}_{page+1}"
            )
        )

    if navigation:
        kb.row(*navigation)

    kb.add(
        types.InlineKeyboardButton(
            "🔢 Go to App Number",
            callback_data=f"jump_{category}"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Categories",
            callback_data="apps"
        )
    )

    return kb


def show_app_list(chat_id, message_id, category, page):

    apps = get_category_apps(category)

    total = len(apps)

    start = page * APPS_PER_PAGE
    end = min(start + APPS_PER_PAGE, total)

    category_name = category.title()

    text = f"""
📱 *{category_name} Apps*

📦 Available: {total}

Showing {start + 1}–{end}

কোনো নির্দিষ্ট App দেখতে চাইলে
তার নম্বর পাঠাতে পারেন।
যেমন: `3`
"""

    bot.edit_message_text(
        text,
        chat_id,
        message_id,
        parse_mode="Markdown",
        reply_markup=app_list_keyboard(category, page)
    )


# =========================================================
# CATEGORY SELECTED
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("appcat_")
)
def category_selected(call):

    category = call.data.replace("appcat_", "")

    # Demo: only business has actual data
    if category != "business":

        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "⬅️ Apps",
                callback_data="apps"
            )
        )

        bot.edit_message_text(
            f"""
📱 *{category.title()} Apps*

এই category-এর service data
এখনো যোগ করা হয়নি।

বর্তমানে Apps-এর মূল flow
test করার জন্য Business category
active করা হয়েছে।
""",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=kb
        )

        return

    show_app_list(
        call.message.chat.id,
        call.message.message_id,
        category,
        0
    )


# =========================================================
# NEXT / PREVIOUS PAGE
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("page_")
)
def change_page(call):

    parts = call.data.split("_")

    category = parts[1]
    page = int(parts[2])

    show_app_list(
        call.message.chat.id,
        call.message.message_id,
        category,
        page
    )


# =========================================================
# APP DETAILS
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("app_")
)
def app_details(call):

    app_id = int(call.data.replace("app_", ""))

    app = next(
        (x for x in APPS if x["id"] == app_id),
        None
    )

    if not app:
        bot.answer_callback_query(
            call.id,
            "App not found."
        )
        return

    kb = types.InlineKeyboardMarkup(row_width=1)

    kb.add(
        types.InlineKeyboardButton(
            "📥 Download",
            callback_data=f"download_{app_id}"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Back to Apps",
            callback_data=f"backapps_{app['category']}"
        )
    )

    text = f"""
📱 *{app["name"]}*

⭐ {app["rating"]}
{app["pricing"]}

━━━━━━━━━━━━━━

📝 {app["description"]}

✨ {app["features"]}
"""

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================================================
# DOWNLOAD OPTIONS
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("download_")
)
def download_options(call):

    app_id = int(call.data.replace("download_", ""))

    app = next(
        (x for x in APPS if x["id"] == app_id),
        None
    )

    if not app:
        return

    kb = types.InlineKeyboardMarkup(row_width=1)

    if app["bot_file"]:

        kb.add(
            types.InlineKeyboardButton(
                "📦 Download from Bot",
                callback_data=f"confirmbot_{app_id}"
            )
        )

    if app["website"]:

        kb.add(
            types.InlineKeyboardButton(
                "🌐 Official Website",
                url=app["website"]
            )
        )

    if app["playstore"]:

        kb.add(
            types.InlineKeyboardButton(
                "▶️ Google Play",
                url=app["playstore"]
            )
        )

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Back",
            callback_data=f"app_{app_id}"
        )
    )

    text = """
📥 *DOWNLOAD*

আপনার পছন্দের download source নির্বাচন করুন।
"""

    if app["bot_file"]:
        text += "\n📦 File available in Smart Hub."

    else:
        text += "\n📦 File is not available in Smart Hub."

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================================================
# CONFIRM BOT DOWNLOAD
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("confirmbot_")
)
def confirm_bot_download(call):

    app_id = int(
        call.data.replace("confirmbot_", "")
    )

    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(
        types.InlineKeyboardButton(
            "✅ Confirm",
            callback_data=f"sendfile_{app_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Cancel",
            callback_data=f"app_{app_id}"
        )
    )

    bot.edit_message_text(
        """
📦 *DOWNLOAD CONFIRMATION*

আপনি কি এই file-টি Smart Hub
থেকে download করতে চান?
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================================================
# SEND FILE
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("sendfile_")
)
def send_file(call):

    app_id = int(
        call.data.replace("sendfile_", "")
    )

    app = next(
        (x for x in APPS if x["id"] == app_id),
        None
    )

    if not app:
        return

    # IMPORTANT:
    # Later replace this with the real Telegram file_id.
    # Example:
    #
    # bot.send_document(
    #     call.message.chat.id,
    #     "TELEGRAM_FILE_ID"
    # )

    bot.send_message(
        call.message.chat.id,
        f"""
📦 *{app["name"]}*

এই prototype-এ এখনো আসল file upload করা হয়নি।

Production version-এ Confirm করার
পর bot সরাসরি stored file পাঠাবে।
""",
        parse_mode="Markdown"
    )


# =========================================================
# JUMP TO APP NUMBER
# =========================================================

user_waiting_for_number = {}


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("jump_")
)
def jump_to_app(call):

    category = call.data.replace("jump_", "")

    user_waiting_for_number[call.from_user.id] = category

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        """
🔢 *APP NUMBER*

আপনি যে App দেখতে চান তার
নম্বর পাঠান।

উদাহরণ:

`30`
""",
        parse_mode="Markdown"
    )


# =========================================================
# NUMBER MESSAGE
# =========================================================

@bot.message_handler(
    func=lambda message:
    message.from_user.id in user_waiting_for_number
)
def receive_app_number(message):

    category = user_waiting_for_number.pop(
        message.from_user.id
    )

    try:
        number = int(message.text.strip())

    except ValueError:

        bot.send_message(
            message.chat.id,
            "❌ শুধু App-এর নম্বর পাঠান। যেমন: 30"
        )
        return

    apps = get_category_apps(category)

    app = next(
        (x for x in apps if x["id"] == number),
        None
    )

    if not app:

        bot.send_message(
            message.chat.id,
            f"❌ {number} নম্বর App পাওয়া যায়নি।"
        )
        return

    show_direct_app(
        message.chat.id,
        app
    )


# =========================================================
# DIRECT APP DETAILS
# =========================================================

def show_direct_app(chat_id, app):

    kb = types.InlineKeyboardMarkup(row_width=1)

    kb.add(
        types.InlineKeyboardButton(
            "📥 Download",
            callback_data=f"download_{app['id']}"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Apps",
            callback_data="apps"
        )
    )

    text = f"""
📱 *{app["name"]}*

⭐ {app["rating"]}
{app["pricing"]}

━━━━━━━━━━━━━━

📝 {app["description"]}

✨ {app["features"]}
"""

    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================================================
# BACK TO APP LIST
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("backapps_")
)
def back_to_apps(call):

    category = call.data.replace(
        "backapps_",
        ""
    )

    show_app_list(
        call.message.chat.id,
        call.message.message_id,
        category,
        0
    )


# =========================================================
# PLACEHOLDER SECTIONS
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data in [
        "bots",
        "software",
        "web",
        "ai"
    ]
)
def placeholder(call):

    names = {
        "bots": "🤖 Telegram Bots",
        "software": "💻 Software",
        "web": "🌐 Web Platforms",
        "ai": "🤖 AI Tools"
    }

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "⬅️ Home",
            callback_data="home"
        )
    )

    bot.edit_message_text(
        f"""
*{names[call.data]}*

এই section-এর functionality
পরবর্তী ধাপে তৈরি করা হবে।

বর্তমানে আমরা শুধু
📱 Apps system test করছি।
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


# =========================================================
# HOME CALLBACK
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "home"
)
def home(call):

    bot.edit_message_text(
        """
🤖 *SMART HUB*

আপনার প্রয়োজনীয় digital service
সহজে খুঁজে নিন।
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# =========================================================
# RUN
# =========================================================

print("🤖 Smart Hub is running...")

bot.infinity_polling(skip_pending=True)
