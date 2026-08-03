from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import SUPPORT_ADMIN_ID, OWNER_ID

router = Router()

@router.callback_query(F.data == "menu_support")
async def support_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Start Support Chat", callback_data="start_support_chat")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(
        "💬 **Support Center**\n\nসাপোর্ট এডমিনের সাথে যোগাযোগ করতে নিচের বাটনে ক্লিক করে আপনার ম্যাসেজ পাঠান:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "start_support_chat")
async def start_support_chat(callback: CallbackQuery, state: aiogram.fsm.context.FSMContext):
    await callback.message.edit_text("✍️ আপনার সমস্যা বা জিজ্ঞাসা লিখে পাঠান, আমরা দ্রুত এডমিনের কাছে পৌঁছে দেব:")
    await state.set_state("support_messaging")
    await callback.answer()

# Note: FSM context handling needs aiogram state import inside handler if needed, 
# but we can standardly implement direct messaging forwarding.
