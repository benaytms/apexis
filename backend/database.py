from backend.models import ImageResponse, WordResponse
from psycopg2.extras import RealDictCursor
import psycopg2
from config import DATABASE_URL, get_today

IMGS_TABLE = "apod_images"
WORDS_TABLE = "words_dict"

def get_today_image() -> ImageResponse | None:
    today = get_today()
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # try today first
            cursor.execute(
                f"SELECT * FROM {IMGS_TABLE} WHERE date = %s", (today,)
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
    today = get_today()
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"SELECT * FROM {WORDS_TABLE} WHERE date = %s", (today,)
            )
            row = cursor.fetchone()

            # fall back
            if not row:
                cursor.execute(
                    f"SELECT * FROM {WORDS_TABLE} ORDER BY date DESC LIMIT 1"
                )
                row = cursor.fetchone()
    return WordResponse(**dict(row)) if row else None
