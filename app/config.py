import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")

    #using sqlite locally for now for ease
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False