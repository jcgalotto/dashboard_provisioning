import os

from dotenv import load_dotenv

load_dotenv()  # carga .env desde la raíz del repo

ORACLE_DSN = os.getenv("ORACLE_DSN", "")
ORACLE_USER = os.getenv("ORACLE_USER", "")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
ORACLE_POOL_MIN = int(os.getenv("ORACLE_POOL_MIN", "1"))
ORACLE_POOL_MAX = int(os.getenv("ORACLE_POOL_MAX", "5"))
JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/var/log/app/app.log")
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*")
VITE_API_BASE = os.getenv("VITE_API_BASE", "/api")
