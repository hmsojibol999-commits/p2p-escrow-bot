from decimal import Decimal
from datetime import datetime
from typing import Optional


class TextFormatters:
    """
    Utility class for formatting currency, numbers, dates, text truncation,
    Telegram markdown sanitization, and user mentions across the bot.
    """

    @staticmethod
    def format_currency(amount: Decimal | float | int, currency: str = "BDT") -> str:
        """
        Formats a numeric amount into a clean currency string with comma separators (e.g., 1,500.00 BDT).
        """
        try:
            dec_amount = Decimal(str(amount))
            formatted_num = f"{dec_amount:,.2f}"
            return f"{formatted_num} {currency.upper()}"
        except Exception:
            return f"0.00 {currency.upper()}"

    @staticmethod
    def format_date(dt: Optional[datetime], format_str: str = "%d-%m-%Y %H:%M") -> str:
        """
        Formats a datetime object into a user-friendly string format.
        """
        if not dt:
            return "N/A"
        return dt.strftime(format_str)

    @staticmethod
    def truncate_text(text: Optional[str], max_length: int = 50) -> str:
        """
        Truncates long text strings with ellipses if they exceed the maximum length.
        """
        if not text:
            return ""
        clean_text = text.strip()
        if len(clean_text) <= max_length:
            return clean_text
        return clean_text[:max_length - 3] + "..."

    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        Escapes special characters for Telegram MarkdownV2 formatting.
        """
        if not text:
            return ""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        escaped = text
        for char in special_chars:
            escaped = escaped.replace(char, f"\\{char}")
        return escaped

    @staticmethod
    def format_user_mention(user_id: int, full_name: Optional[str]) -> str:
        """
        Generates an HTML-style clickable user mention for Telegram messages.
        """
        safe_name = full_name.replace("<", "&lt;").replace(">", "&gt;") if full_name else "User"
        return f"<a href='tg://user?id={user_id}'>{safe_name}</a>"
        
