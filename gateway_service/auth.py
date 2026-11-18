import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv

# Load root .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

SECRET_KEY = os.getenv("JWT_SECRET", "").strip()
if not SECRET_KEY:
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: 'JWT_SECRET' is not defined in the .env file! "
        "Every secret key must be stored in .env only."
    )

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Generates a secure signed JWT token containing user identity details and returns (token, expire)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token, expire

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT token. Returns payload if valid, None if expired/corrupted."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
