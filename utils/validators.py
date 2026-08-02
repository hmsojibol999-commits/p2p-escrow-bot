import re
from decimal import Decimal, InvalidOperation
from typing import Tuple, Union


class InputValidators:
    """
    Utility class for validating user inputs such as PINs, phone numbers,
    amounts, transaction IDs, and usernames across the bot workflows.
    """

    @staticmethod
    def validate_pin(pin: str) -> Tuple[bool, str]:
        """
        Validates that a financial PIN is a 4 to 6 digit numeric string.
        """
        if not pin or not pin.isdigit():
            return False, "PIN must contain only numbers."
        if not (4 <= len(pin) <= 6):
            return False, "PIN must be between 4 and 6 digits long."
        return True, "Valid PIN."

    @staticmethod
    def validate_bdt_phone(phone: str) -> Tuple[bool, str]:
        """
        Validates a Bangladeshi mobile phone number format.
        Accepts formats like: 01712345678, +8801712345678, 8801712345678
        """
        if not phone:
            return False, "Phone number cannot be empty."
        
        cleaned = phone.strip().replace(" ", "").replace("-", "")
        
        # Regex pattern for Bangladeshi mobile operators (Grameenphone, Banglalink, Robi, Airtel, Teletalk)
        pattern = r"^(?:\+?88)?01[3-9]\d{8}$"
        
        if re.match(pattern, cleaned):
            return True, "Valid mobile number."
        return False, "Invalid Bangladeshi mobile number format."

    @staticmethod
    def validate_decimal_amount(amount_str: str) -> Tuple[bool, str, Decimal]:
        """
        Validates a string input to ensure it represents a valid, positive Decimal amount.
        Returns a tuple: (is_valid, error_message, decimal_value)
        """
        if not amount_str:
            return False, "Amount cannot be empty.", Decimal("0.00")

        clean_str = amount_str.strip().replace(",", "")

        try:
            val = Decimal(clean_str)
            if val <= Decimal("0.00"):
                return False, "Amount must be strictly greater than zero.", Decimal("0.00")
            
            if val > Decimal("10000000.00"):
                return False, "Amount exceeds maximum transaction limit.", Decimal("0.00")
            
            # Check maximum decimal precision (up to 2 decimal places)
            if val.as_tuple().exponent < -2:
                return False, "Amount cannot have more than 2 decimal places.", Decimal("0.00")

            return True, "Valid amount.", val
        except InvalidOperation:
            return False, "Invalid numeric format entered.", Decimal("0.00")

    @staticmethod
    def validate_amount(amount_str: str) -> tuple[bool, Union[Decimal, str]]:
        """
        Alternative clean amount validator returning (is_valid, parsed_amount_or_error_message).
        """
        is_valid, err_msg, dec_val = InputValidators.validate_decimal_amount(amount_str)
        if is_valid:
            return True, dec_val
        return False, err_msg

    @staticmethod
    def validate_transaction_id(trx_id: str) -> tuple[bool, str]:
        """
        Validates transaction ID or hash length and alphanumeric characters.
        """
        if not trx_id:
            return False, "Transaction ID cannot be empty."

        cleaned_trx = trx_id.strip()
        if len(cleaned_trx) < 6 or len(cleaned_trx) > 64:
            return False, "Transaction ID length is invalid (must be between 6 and 64 characters)."

        # Check alphanumeric / standard transaction formatting
        if not re.match(r"^[a-zA-Z0-9_-]+$", cleaned_trx):
            return False, "Transaction ID contains invalid characters. Use letters and numbers only."

        return True, cleaned_trx

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """
        Validates telegram username formatting.
        """
        if not username:
            return False, "Username cannot be empty."

        cleaned = username.strip().lstrip("@")
        if not re.match(r"^[a-zA-Z0-9_]{5,32}$", cleaned):
            return False, "Invalid username format (must be 5-32 characters long)."

        return True, cleaned
        
