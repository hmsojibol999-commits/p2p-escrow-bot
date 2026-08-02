from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


class ReplyKeyboards:
    """
    Persistent Reply Keyboards Generator for Telegram Marketplace Bot.
    Provides bottom-bar persistent control buttons for quick access.
    """

    @staticmethod
    def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
        """
        Generates the standard persistent bottom reply keyboard.
        """
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="🏠 Main Menu"),
                    KeyboardButton(text="💼 My Wallet"),
                ],
                [
                    KeyboardButton(text="🛍️ Marketplace"),
                    KeyboardButton(text="🎫 Support"),
                ],
            ],
            resize_keyboard=True,
            is_persistent=True,
            input_field_placeholder="Choose an option from the menu below...",
        )

    @staticmethod
    def get_contact_share_keyboard() -> ReplyKeyboardMarkup:
        """
        Generates a keyboard requesting phone number verification.
        """
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📱 Share Phone Number", request_contact=True)
                ],
                [
                    KeyboardButton(text="❌ Cancel")
                ],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder="Please share your phone number to verify...",
        )
      
