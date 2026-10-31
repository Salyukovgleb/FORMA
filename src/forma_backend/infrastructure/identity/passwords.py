"""Versioned, bounded scrypt hashes using the standard library only."""

import hashlib
import hmac
import secrets
from threading import BoundedSemaphore


from forma_backend.modules.identity.application import PasswordCapacityExceeded


class ScryptPasswordHasher:
    _slots = BoundedSemaphore(2)

    def _derive(self, password: str, salt: bytes) -> bytes:
        if not self._slots.acquire(blocking=False):
            raise PasswordCapacityExceeded()
        try:
            return hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt,
                n=32768,
                r=8,
                p=1,
                maxmem=64 * 1024 * 1024,
                dklen=64,
            )
        finally:
            self._slots.release()

    def hash(self, password: str) -> str:
        if not 12 <= len(password) <= 128:
            raise ValueError("Password length outside policy")
        salt = secrets.token_bytes(16)
        digest = self._derive(password, salt)
        return f"scrypt$v1$32768$8$1${salt.hex()}${digest.hex()}"

    def verify(self, password: str, encoded: str) -> bool:
        if len(password) > 128 or len(encoded) > 256:
            return False
        parts = encoded.split("$")
        if len(parts) != 7 or parts[:5] != ["scrypt", "v1", "32768", "8", "1"]:
            return False
        try:
            salt = bytes.fromhex(parts[5])
            expected = bytes.fromhex(parts[6])
        except ValueError:
            return False
        if len(salt) != 16 or len(expected) != 64:
            return False
        return hmac.compare_digest(self._derive(password, salt), expected)
