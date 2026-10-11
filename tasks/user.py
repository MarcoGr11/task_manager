"""User profile with personal data (Lab 4)."""
import hashlib
import secrets
from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    email: str
    phone: str
    password_hash: str | None  # never returned outside (export, logs, API responses)
    reset_token: str | None  # never returned outside
    marketing_opt_in_source: str = "signup_form"
    is_admin: bool = False  # internal security flag, never exported
    anonymized_at: str | None = None


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"
