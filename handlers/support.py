from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from config import SUPPORT_ADMIN_ID, OWNER_ID

router = Router()

class SupportStates(StatesGroup):
    chatting = State()

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
async def start_support_chat_fsm(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✍️ আপনার সমস্যা বা প্রশ্ন সরাসরি লিখে পাঠান:")
    await state.set_state(SupportStates.chatting)
    await callback.answer()

@router.message(SupportStates.chatting)
async def forward_to_support(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/"):
        return
    
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    target_admin = SUPPORT_ADMIN_ID if SUPPORT_ADMIN_ID else OWNER_ID
    if target_admin:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Reply to User", callback_data=f"support_reply_{user_id}")]
        ])
        await message.bot.send_message(
            target_admin,
            f"💬 **Support Message from User**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"🔗 Username: @{username}\n\n"
            f"✉️ Message:\n{message.text}",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        await message.answer("✅ আপনার ম্যাসেজ সাপোর্ট টিমের কাছে পাঠানো হয়েছে। খুব শীঘ্রই উত্তর পাবেন।")
    else:
        await message.answer("⚠️ বর্তমানে কোনো সাপোর্ট এডমিন উপলব্ধ নেই।")
    
    await state.clear()
    
