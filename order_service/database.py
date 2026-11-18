import os
import pymysql
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load root-level .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
raw_password = os.getenv("MYSQL_PASSWORD", "")
MYSQL_PASSWORD = quote_plus(raw_password)
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE_ORDERS", "orders_db")

# Proactively ensure database exists in MySQL before creating engine
try:
    _conn = pymysql.connect(
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        user=MYSQL_USER,
        password=raw_password,
        connect_timeout=3
    )
    with _conn.cursor() as _cursor:
        _cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    _conn.commit()
    _conn.close()
except Exception as _e:
    print(f"[{MYSQL_DATABASE}] Auto-creation notice: {_e}")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

