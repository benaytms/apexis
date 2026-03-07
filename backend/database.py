import sqlite3 as sql3
from datetime import date
from backend.models import ImageResponse, WordResponse
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "../apod_words.db")
IMGS_TABLE = "apod_images"
WORDS_TABLE = "words_dict"

def get_today_image():
    today = date.today().isoformat()
    with sql3.connect(DB_NAME) as conn:
        conn.row_factory = sql3.Row
        row = conn.execute(
            f"SELECT * FROM {IMGS_TABLE} WHERE date=?", (today,)
        ).fetchone()
    return ImageResponse(**dict(row)) if row else None

def get_today_word():
    with sql3.connect(DB_NAME) as conn:
        conn.row_factory = sql3.Row
        row = conn.execute(
            f"SELECT * FROM {WORDS_TABLE} ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return WordResponse(**dict(row)) if row else None