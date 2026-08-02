from decimal import Decimal
from typing import Optional


class TextFormatters:
    """
    Utility class for formatting currency, numbers, text truncation,
    and Telegram markdown sanitization.
    """

    @staticmethod
    def format_currency(amount: Decimal, currency_symbol: str = "BDT") -> str:
        """
        Formats a Decimal amount into a readable currency string with comma separators.
        Example: 1500.5 -> "1,500.50 BDT"
        """
        try:
            dec_val = Decimal(str(amount))
            formatted_num = f"{dec_val:,.2f}"
            return f"{formatted_num} {currency_symbol}"
        except Exception:
            return f"0.00 {currency_symbol}"

    @staticmethod
    def truncate_text(text: Optional[str], max_length: int = 50) -> str:
        """
        Truncates long strings to a specified maximum length and appends ellipsis.
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
    def format_user_mention(user_id: int, full_name: str) -> str:
        """
        Generates an HTML-style clickable user mention for Telegram messages.
        """
        safe_name = full_name.replace("<", "<").replace(">", ">") if full_name else "User"
        return f"<a href='tg://user?id={user_id}'>{safe_name}</a>"
      
