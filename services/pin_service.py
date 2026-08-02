import hashlib
import os
import secrets
from typing import Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user_pin import UserPin


class PinService:
    """
    User Financial PIN Management Service.
    Handles PIN hashing using PBKDF2-HMAC-SHA256 with cryptographically secure random salts,
    verification for sensitive transactions (Withdraw/Transfer), and secure reset logic.
    """

    ITERATIONS = 100_000

    @classmethod
    def hash_pin(cls, pin: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """
        Hashes a raw numeric PIN using PBKDF2-SHA256.
        Returns a tuple: (hex_hash, hex_salt)
        """
        if not salt:
            salt = secrets.token_bytes(16)

        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            salt,
            cls.ITERATIONS
        )
        return derived_key.hex(), salt.hex()

    @classmethod
    def verify_pin(cls, raw_pin: str, stored_hash: str, stored_salt_hex: str) -> bool:
        """
        Verifies if a raw input PIN matches the stored hash and salt.
        Uses constant-time comparison to prevent timing attacks.
        """
        try:
            salt = bytes.fromhex(stored_salt_hex)
            computed_hash, _ = cls.hash_pin(raw_pin, salt)
            return secrets.compare_digest(computed_hash, stored_hash)
        except Exception:
            return False

    @staticmethod
    async def set_user_pin(
        session: AsyncSession, user_id: int, pin: str
    ) -> Tuple[bool, str]:
        """
        Sets or updates a user's financial security PIN.
        Must be a 4 to 6 digit numeric string.
        """
        if not pin.isdigit() or not (4 <= len(pin) <= 6):
            return False, "PIN must be a 4 to 6 digit numeric code."

        stmt = select(UserPin).where(UserPin.user_id == user_id)
        result = await session.execute(stmt)
        user_pin_record = result.scalar_one_or_none()

        pin_hash, salt_hex = PinService.hash_pin(pin)

        if user_pin_record:
            user_pin_record.pin_hash = pin_hash
            user_pin_record.salt = salt_hex
            user_pin_record.is_set = True
        else:
            user_pin_record = UserPin(
                user_id=user_id,
                pin_hash=pin_hash,
                salt=salt_hex,
                is_set=True
            )
            session.add(user_pin_record)

        await session.commit()
        return True, "Financial security PIN set successfully."

    @staticmethod
    async def check_user_pin(
        session: AsyncSession, user_id: int, input_pin: str
    ) -> Tuple[bool, str]:
        """
        Verifies a user's PIN for a sensitive financial action.
        """
        stmt = select(UserPin).where(UserPin.user_id == user_id)
        result = await session.execute(stmt)
        user_pin_record = result.scalar_one_or_none()

        if not user_pin_record or not user_pin_record.is_set:
            return False, "PIN_NOT_SET"

        is_valid = PinService.verify_pin(
            input_pin, user_pin_record.pin_hash, user_pin_record.salt
        )

        if is_valid:
            return True, "PIN verified successfully."
        else:
            return False, "Incorrect security PIN entered."
          
