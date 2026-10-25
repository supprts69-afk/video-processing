# backend/app/database.py
import os
from databases import Database

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# যদি আগের কোনো query string থেকে থাকে, তবে সেটি বাদ দিয়ে ফ্রেশ URL নেওয়া হচ্ছে
if "?" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

# URL-এর বদলে সরাসরি পাইথন আর্গুমেন্ট হিসেবে statement_cache_size=0 পাস করা হলো
# এটি asyncpg ড্রাইভারকে বাধ্য করবে Prepared Statement ব্যবহার না করতে
database = Database(
    DATABASE_URL,
    statement_cache_size=0
)

async def get_db_connection():
    """
    FastAPI ডিপেন্ডেন্সি যা রাউটারগুলোতে ডাটাবেস কানেকশন পাস করবে।
    """
    return database
