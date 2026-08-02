import re
from decimal import Decimal, InvalidOperation
from typing import Tuple


class InputValidators:
    """
    Utility class for validating user inputs such as PINs, phone numbers,
    amounts, and identifiers across the bot workflows.
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
            
            # Check maximum decimal precision (up to 2 decimal places)
            if val.as_tuple().exponent < -2:
                return False, "Amount cannot have more than 2 decimal places.", Decimal("0.00")

            return True, "Valid amount.", val
        except InvalidOperation:
            return False, "Invalid numeric format entered.", Decimal("0.00")
          
