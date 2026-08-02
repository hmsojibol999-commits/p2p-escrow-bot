from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Tuple


class InlineKeyboards:
    """
    Centralized Inline Keyboard Generator for Telegram Marketplace Bot.
    Provides standard and dynamic keyboard markups for navigation, wallets, and orders.
    """

    @staticmethod
    def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
        """
        Generates the main navigation menu keyboard.
        """
        keyboard = [
            [
                InlineKeyboardButton(text="🛍️ Marketplace", callback_data="market_home"),
                InlineKeyboardButton(text="💼 My Wallet", callback_data="wallet_home"),
            ],
            [
                InlineKeyboardButton(text="📦 My Orders", callback_data="user_orders"),
                InlineKeyboardButton(text="👥 Referrals", callback_data="user_referrals"),
            ],
            [
                InlineKeyboardButton(text="🎫 Support Ticket", callback_data="support_home"),
                InlineKeyboardButton(text="⚙️ Settings", callback_data="user_settings"),
            ],
        ]

        if is_admin:
            keyboard.append([
                InlineKeyboardButton(text="🔐 Admin Panel", callback_data="admin_dashboard")
            ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_wallet_keyboard() -> InlineKeyboardMarkup:
        """
        Generates wallet options keyboard (Deposit, Withdraw, Transfer, History).
        """
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="➕ Deposit Balance", callback_data="wallet_deposit"),
                    InlineKeyboardButton(text="📤 Withdraw Funds", callback_data="wallet_withdraw"),
                ],
                [
                    InlineKeyboardButton(text="💸 P2P Transfer", callback_data="wallet_transfer"),
                    InlineKeyboardButton(text="📜 Ledger History", callback_data="wallet_history"),
                ],
                [
                    InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="main_menu")
                ],
            ]
        )

    @staticmethod
    def get_deposit_methods_keyboard() -> InlineKeyboardMarkup:
        """
        Generates local and crypto deposit gateway selection keyboard.
        """
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🇧🇩 bKash", callback_data="dep_bkash"),
                    InlineKeyboardButton(text="🇧🇩 Nagad", callback_data="dep_nagad"),
                ],
                [
                    InlineKeyboardButton(text="🇧🇩 Rocket", callback_data="dep_rocket"),
                    InlineKeyboardButton(text="🟡 Binance Pay", callback_data="dep_binance"),
                ],
                [
                    InlineKeyboardButton(text="🔙 Back to Wallet", callback_data="wallet_home")
                ],
            ]
        )

    @staticmethod
    def get_back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
        """
        Generates a simple single back button markup.
        """
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back", callback_data=callback_data)]
            ]
        )
      
