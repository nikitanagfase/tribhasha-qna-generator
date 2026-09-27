"""
database.py
------------
Minimal, dependency-free authentication for the Streamlit app.
Passwords are never stored in plain text: each one gets a random salt
and is hashed with PBKDF2-HMAC-SHA256 before hitting SQLite.
"""

import sqlite3
import hashlib
import os
import secrets

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tribhasha_users.db",
)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 100_000
    ).hex()


def register_user(username: str, password: str):
    username = (username or "").strip()
    if not username or not password:
        return False, "Username and password cannot be empty."
    if len(password) < 4:
        return False, "Password should be at least 4 characters long."

    conn = sqlite3.connect(DB_PATH)
    try:
        existing = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            return False, "This username is already taken."

        salt = secrets.token_hex(16)
        password_hash = _hash_password(password, salt)
        conn.execute(
            "INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
            (username, salt, password_hash),
        )
        conn.commit()
        return True, "Account created successfully."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()


def verify_user(username: str, password: str):
    username = (username or "").strip()
    if not username or not password:
        return False, "Username and password cannot be empty."

    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT salt, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not row:
            return False, "No account found with this username."

        salt, stored_hash = row
        computed_hash = _hash_password(password, salt)
        if secrets.compare_digest(computed_hash, stored_hash):
            return True, "Login successful."
        return False, "Incorrect password."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()
