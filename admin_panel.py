import sqlite3
import os
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID", "6226350422"))

def get_connection():
    conn = sqlite3.connect("bot_database.db")
    conn.row_factory = sqlite3.Row
    return conn

class AdminState(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_category_desc = State()
    waiting_for_filter_name = State()

# 👑 ADMIN PANEL COMMAND
@admin_router.message(Command("admin"))
async def admin_panel_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⚠️ Apni ei command-ti babohar korar jonno authorized non.")
        return

    text = "👑 **DYNAMIC ADMIN CONTROL PANEL**\n\nNicher option-gulo theke marketplace control করুন:"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 Manage Categories", callback_data="admin_cats")],
        [InlineKeyboardButton(text="⚙️ Dynamic Filters", callback_data="admin_filters")],
        [InlineKeyboardButton(text="🏪 Seller Requests", callback_data="admin_sellers")],
        [InlineKeyboardButton(text="❌ Close", callback_data="close_admin")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# 📁 CATEGORY MANAGEMENT
@admin_router.callback_query(F.data == "admin_cats")
async def manage_categories(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    cats = cursor.fetchall()
    conn.close()

    cat_list_text = "📁 **CURRENT CATEGORIES:**\n\n"
    if not cats:
        cat_list_text += "*(Kono category toiri kora nai)*"
    else:
        for c in cats:
            status = "🟢 Active" if c["is_active"] else "🔴 Inactive"
            cat_list_text += f"• **{c['name']}** ({status})\n_{c['description'] or 'No desc'}_\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add New Category", callback_data="add_cat")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_admin")]
    ])
    await callback.message.edit_text(cat_list_text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@admin_router.callback_query(F.data == "add_cat")
async def add_cat_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.waiting_for_category_name)
    await callback.message.edit_text("📝 Notun **Category Name** likhun (e.g. Gmail, Facebook 2FA, TikTok):")
    await callback.answer()

@admin_router.message(AdminState.waiting_for_category_name)
async def process_cat_name(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(cat_name=message.text.strip())
    await state.set_state(AdminState.waiting_for_category_desc)
    await message.answer("📝 Ei category-er shonkhiptho **Description** likhun (Athoba 'None' likhun):")

@admin_router.message(AdminState.waiting_for_category_desc)
async def process_cat_desc(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    cat_name = data.get("cat_name")
    desc = message.text.strip()
    if desc.lower() == "none":
        desc = ""

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name, description) VALUES (?, ?)", (cat_name, desc))
        conn.commit()
        await message.answer(f"✅ **Category '{cat_name}' successfully added!**")
    except sqlite3.IntegrityError:
        await message.answer(f"⚠️ Category '{cat_name}' agge thekei ache!")
    finally:
        conn.close()

    await state.clear()

@admin_router.callback_query(F.data == "close_admin")
async def close_admin(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@admin_router.callback_query(F.data == "back_admin")
async def back_admin(callback: types.CallbackQuery):
    text = "👑 **DYNAMIC ADMIN CONTROL PANEL**\n\nNicher option-gulo theke marketplace control করুন:"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 Manage Categories", callback_data="admin_cats")],
        [InlineKeyboardButton(text="⚙️ Dynamic Filters", callback_data="admin_filters")],
        [InlineKeyboardButton(text="🏪 Seller Requests", callback_data="admin_sellers")],
        [InlineKeyboardButton(text="❌ Close", callback_data="close_admin")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()
  
