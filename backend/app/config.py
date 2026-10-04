import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine import URL

# Load .env from backend root or workspace root
backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / '.env')
load_dotenv(backend_dir.parent / '.env')

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "prod-market-reviewer-secret-key-99214")
    
    # Database configuration
        # Database configuration
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DB = os.getenv("MYSQL_DATABASE", "marketplace_reviewer")

    DEFAULT_MYSQL_URI = URL.create(
        drivername="mysql+pymysql",
        username=MYSQL_USER,
        password=MYSQL_PASSWORD,
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=MYSQL_DB,
    )

    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URI")
        or DEFAULT_MYSQL_URI
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    # Aiven MySQL SSL configuration
    MYSQL_SSL_CA = os.getenv("MYSQL_SSL_CA", "")

    if MYSQL_SSL_CA:
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {
            "ssl": {
                "ca": MYSQL_SSL_CA
            }
        }

    # AI Provider configuration (Groq)
    AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    # Legacy/Fallback configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    # Listing Validation configuration
    MAX_TITLE_LENGTH = int(os.getenv("MAX_TITLE_LENGTH", "150"))
    MIN_TITLE_LENGTH = int(os.getenv("MIN_TITLE_LENGTH", "5"))
    MAX_DESC_LENGTH = int(os.getenv("MAX_DESC_LENGTH", "5000"))
    MIN_DESC_LENGTH = int(os.getenv("MIN_DESC_LENGTH", "20"))
    
    ALLOWED_CATEGORIES = [
        "Electronics & Gadgets",
        "Home & Kitchen",
        "Health & Personal Care",
        "Fashion & Apparel",
        "Beauty & Cosmetics",
        "Sports & Outdoors",
        "Books & Media",
        "Automotive & Tools",
        "Toys & Games",
        "Services & Consulting",
        "General Merchandise"
    ]

    ALLOWED_CURRENCIES = ["INR", "USD", "EUR", "GBP", "CAD", "AUD"]
    ALLOWED_LISTING_TYPES = ["Product", "Service"]

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    AI_PROVIDER = "groq"
    GROQ_API_KEY = "test-mock-key"
    GROQ_MODEL = "openai/gpt-oss-20b"
    GEMINI_API_KEY = "test-mock-key"
    SQLALCHEMY_ENGINE_OPTIONS = {}
