from backend.models import ImageResponse, WordResponse
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
import psycopg2
import os

load_dotenv()

TODAY = datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()
DATABASE_URL = str(os.getenv('DATABASE_URL'))
IMGS_TABLE = "apod_images"
WORDS_TABLE = "words_dict"

def get_today_image() -> ImageResponse | None:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # try today first
            cursor.execute(
                f"SELECT * FROM {IMGS_TABLE} WHERE date = %s", (TODAY,)
            )
            row = cursor.fetchone()
            
            # fall back
            if not row:
                cursor.execute(
                    f"SELECT * FROM {IMGS_TABLE} ORDER BY date DESC LIMIT 1"
                )
                row = cursor.fetchone()
    return ImageResponse(**dict(row)) if row else None

def get_today_word() -> WordResponse | None:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"SELECT * FROM {WORDS_TABLE} WHERE date = %s", (TODAY,)
            )
            row = cursor.fetchone()

            # fall back
            if not row:
                cursor.execute(
                    f"SELECT * FROM {WORDS_TABLE} ORDER BY date DESC LIMIT 1"
                )
                row = cursor.fetchone()
    return WordResponse(**dict(row)) if row else None
