import os
from databases import Database

# Supabase URL-এ 'postgres://' থাকলে তা 'postgresql://'-এ পরিবর্তন করা (asyncpg এর জন্য)
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ডাটাবেস ইনস্ট্যান্স তৈরি
database = Database(DATABASE_URL)

async def get_db_connection():
    """
    FastAPI ডিপেন্ডেন্সি যা রাউটারগুলোতে ডাটাবেস কানেকশন পাস করবে।
    """
    return database
