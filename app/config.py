import os
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Instance folder (for local runtime files like SQLite DB)
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")

    #using sqlite locally for now for ease
    SQLALCHEMY_DATABASE_URI = os.environ.get(
         "DATABASE_URL",
        f"sqlite:///{(INSTANCE_DIR / 'local.db').as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #session and cookie security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    #keep this false for local http dev, when in App Engine set to true as it is https
    SESSION_COOKIE_SECURE = False