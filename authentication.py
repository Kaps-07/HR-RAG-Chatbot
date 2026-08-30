"""
authentication.py - User registration and login for HR Assistant.

MongoDB stores user documents with fields: email, password (hashed), role.
Passwords are hashed with bcrypt via passlib — never stored as plain text.
"""
import os
from pymongo import MongoClient
from passlib.context import CryptContext

# ---------------------------------------------------------------------------
# MongoDB connection  (same config as before)
# ---------------------------------------------------------------------------
MONGO_URL = os.environ.get("MONGO_CLIENT")

db_name = "hr_assistant"
user_collection_name = "collection_user"

client = MongoClient(MONGO_URL)
db = client[db_name]
user_collection = db[user_collection_name]


# ---------------------------------------------------------------------------
# Password hashing  (bcrypt)
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plain password matches the stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# User operations
# ---------------------------------------------------------------------------

def register_user(email: str, password: str, role: str):
    """
    Register a new user.

    Returns:
        (True,  "Registered successfully.")   on success
        (False, "<reason>")                    on failure
    """
    email = email.strip().lower()

    if role not in ("hr", "employee"):
        return False, "Role must be 'hr' or 'employee'."

    if user_collection.find_one({"email": email}):
        return False, "An account with this email already exists."

    user_collection.insert_one({
        "email": email,
        "password": hash_password(password),   # never store plain text
        "role": role,
    })
    return True, "Account created successfully."


def login_user(email: str, password: str):
    """
    Validate login credentials.

    Returns:
        (True,  {"email": ..., "role": ...})   on success  (no password returned)
        (False, "<reason>")                     on failure
    """
    email = email.strip().lower()
    user = user_collection.find_one({"email": email})

    if not user:
        return False, "Invalid email or password."

    if not verify_password(password, user["password"]):
        return False, "Invalid email or password."

    # Return only safe fields — the password hash is never passed back
    return True, {"email": user["email"], "role": user["role"]}
