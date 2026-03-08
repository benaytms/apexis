import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime
from zoneinfo import ZoneInfo
from backend.models import ImageResponse, WordResponse
import os

DATABASE_URL = str(os.getenv('DATABASE_URL'))
IMGS_TABLE = "apod_images"
WORDS_TABLE = "words_dict"

def get_today_image() -> ImageResponse | None:
    today = datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"SELECT * FROM {IMGS_TABLE} WHERE date = %s", (today,)
            )
            row = cursor.fetchone()
    return ImageResponse(**dict(row)) if row else None

def get_today_word() -> WordResponse | None:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"SELECT * FROM {WORDS_TABLE} ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
    return WordResponse(**dict(row)) if row else None
