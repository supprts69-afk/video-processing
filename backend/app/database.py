# backend/app/database.py
import os
from databases import Database

# URL ঠিক করা
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Supabase PgBouncer (পোর্ট 6543) এর Prepared Statement সমস্যা সমাধানের জন্য
# statement_cache_size=0 যুক্ত করা হলো
if DATABASE_URL and "statement_cache_size" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL += f"{separator}statement_cache_size=0&prepared_statement_cache_size=0"

# ডাটাবেস ইনস্ট্যান্স তৈরি
database = Database(DATABASE_URL)

async def get_db_connection():
    """
    FastAPI ডিপেন্ডেন্সি যা রাউটারগুলোতে ডাটাবেস কানেকশন পাস করবে।
    """
    return database
