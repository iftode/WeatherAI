import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "weather-secret-key")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    MAX_ROWS = int(os.getenv("MAX_ROWS", "200"))

    EXPORT_DIR = os.getenv("EXPORT_DIR", "exports")
    LOG_DIR = os.getenv("LOG_DIR", "logs")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "baza_meteo")
