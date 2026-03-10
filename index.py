"""
APEXIS - Daily pipeline script

Fetches NASA APOD and a random English word,
stores them in a Postgresql Database, and sends
a Discord notification on completion.

Author: Benay Tomas

Created: 2026-03-06

Last edited: 2026-03-09

Version: 1.0.3
"""

from random import randint
import requests as rq
import psycopg2
import logging
from config import NASA_API, DATABASE_URL, DISCORD_WEBHOOK, get_today

logging.basicConfig(
    level= logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)

logger = logging.getLogger(__name__)

APOD_URL = "https://api.nasa.gov/planetary/apod?api_key=" + NASA_API
DICT_URL = "https://api.dictionaryapi.dev/api/v2/entries/en"
RANDOMWORD_URL = "https://random-words-api.kushcreates.com/api?language=en"

ALLOWED_TABLES = ("apod_images", "words_dict")


def send_notification(subject:str, body:str) -> None:
    """
    Sends an email notification via .
    """
    try:
        msg = f"**{subject}**\n\n{body}"
        response = rq.post(DISCORD_WEBHOOK, json={"content": msg})
        if response.status_code == 204:
            logger.info("Notification sent!")
        else:
            logger.error(f"Notification failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send notification, error: {e}")


def word_exists(word:str) -> bool:
    """
    Checks if word is already in the Data Base.
    Returns False if table doesn't exist yet.
    """
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM words_dict WHERE word = %s", (word,)
                )
                return cursor.fetchone() is not None
    except Exception:
        return False


def drop_table(table_name:str) -> None:
    """
    Drops table from Data Base.
    """
    try:
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Unknown table: '{table_name}'")

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"DROP TABLE {table_name};")
                logger.warning(f"Table {table_name} dropped.")

    except Exception as e:
        logger.error(f"Could not drop table, error: {e}")


def print_table(table_name:str, limit:int = 10) -> None:
    """
    Prints specified table for debugging purposes.
    """
    try:
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Unknown table: '{table_name}'")

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
                rows = cursor.fetchall()
                logger.debug(f"Table {table_name}:")
                for row in rows:
                    logger.debug(row)

    except Exception as e:
        logger.error(f"Could not print table, error: {e}")


def generate_word() -> list:
    """
    Generates a random word using the Random Words API, then
    passes it to the Free Dictionary API to get its definition.
    Skips words already in the database.
    Limit of 50 attempts before falling back to 'default'.
    """
    max_attempts = 50

    for attempt in range(max_attempts):

        word_response = rq.get(RANDOMWORD_URL, timeout=5)

        if word_response.status_code != 200:
            continue

        try:
            word_data = word_response.json()
            n = randint(0, len(word_data) - 1)
            random_word = word_data[n]['word']

            if word_exists(random_word):
                logger.debug(f"Word '{random_word}' already in database, trying again...")
                continue

            dict_response = rq.get(f"{DICT_URL}/{random_word}", timeout=5)
            dict_data = dict_response.json()

            if isinstance(dict_data, list):
                logger.debug(f"Found valid word: {random_word}")
                return dict_data
            else:
                logger.info(f"Word '{random_word}' not available, trying again...")
                continue

        except Exception as e:
            logger.error(f"Could not generate word, error: {e}")

    return ['default']
        

def img_to_table(img_otd:dict, table_name:str) -> bool:
    """
    Inserts APOD information into the images table.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Unknown table: '{table_name}'")

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        title TEXT UNIQUE NOT NULL,
                        date TEXT UNIQUE NOT NULL,
                        explanation TEXT NOT NULL,
                        url TEXT NOT NULL,
                        copyright TEXT NOT NULL,
                        media_type TEXT NOT NULL DEFAULT 'image'
                    )
                ''')

                cursor.execute(
                    f"SELECT 1 FROM {table_name} WHERE date = %s", (img_otd['date'],)
                )
                if not cursor.fetchone():
                    cursor.execute(f'''
                        INSERT INTO {table_name}
                            (title, date, explanation, url, copyright, media_type)
                        VALUES
                            (%s, %s, %s, %s, %s, %s)
                        ''',
                        (img_otd['title'], img_otd['date'],
                         img_otd['explanation'], img_otd['url'],
                         img_otd['copyright'], img_otd['media_type'])
                    )
                    logger.info(f"Image '{img_otd['title']}' added to database.")
                    return True
                else:
                    logger.info(f"Today's image already in database, skipping.")
                    return False
            except Exception as e:
                logger.error(f"Could not insert image to data base, error: {e}")
                raise


def word_to_table(word_otd:dict, table_name:str) -> bool:
    """
    Inserts word information into the words table.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Unknown table: '{table_name}'")

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        word TEXT UNIQUE NOT NULL,
                        definition TEXT NOT NULL,
                        date TEXT UNIQUE NOT NULL
                    )
                ''')

                cursor.execute(
                    f"SELECT 1 FROM {table_name} WHERE date = %s", (word_otd['date'],)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        f"INSERT INTO {table_name} (word, definition, date) VALUES (%s, %s, %s)",
                        (word_otd['word'], word_otd['definition'], word_otd['date'])
                    )
                    logger.info(f"Word {word_otd['word']} added to database.")
                    return True
                else:
                    logger.info(f"Today's word already in database, skipping.")
                    return False
            except Exception as e:
                logger.error(f"Failed to insert word to database, error: {e}")
                raise


def parse_img_data(img_data:dict) -> dict:
    return {
        "title": img_data.get('title', 'No title'),
        "date": img_data.get('date', '01-01-0001'),
        "explanation": img_data.get('explanation', 'No explanation'),
        "url": img_data.get('url', 'No url'),
        "copyright": img_data.get('copyright', 'NASA, ESA, CSA, STScI'),
        "media_type": img_data.get('media_type', 'image')
    }

def parse_word_data(dict_data:list) -> dict:
    if dict_data[0] == 'default':
        logger.warning("Could not generate a valid word today, using default.")
        return {
            "word": 'default',
            "definition": 'automatic or standard way of acting or responding.',
            "date": get_today()
        }
        
    word = dict_data[0].get("word")
    meanings=dict_data[0]['meanings']
    definitions = []
    for meaning in meanings:
        for definition in meaning['definitions']:
            definitions.append(definition['definition'])
    definitions_result = " ; ".join(definitions[:3]).rstrip('.')

    return {
        "word": word,
        "definition": definitions_result,
        "date": get_today()
    }


def main(drop_tables:bool = False) -> None:
    """
    Main function — integrates everything into one place.
    """
    IMGS_TABLE = ALLOWED_TABLES[0]
    WORDS_TABLE = ALLOWED_TABLES[1]
    inserted_img = False
    inserted_word = False

    # drop ALL tables if requested
    if drop_tables:
        drop_table(IMGS_TABLE)
        drop_table(WORDS_TABLE)
        logger.warning('All tables dropped!')
        exit(1)

    # fetch NASA APOD
    response = rq.get(APOD_URL, timeout=10)

    if response.status_code == 200:
        img_otd = response.json()
        logger.info("Request successful")
    else:
        logger.error(f"An error occurred: {response.status_code}")
        send_notification(
            subject="⚠️ APEXIS Script Failed",
            body="NASA API request failed."
        )
        exit(1)

    # build image dict
    img_otd = parse_img_data(img_otd)

    try:
        inserted_img = img_to_table(img_otd, IMGS_TABLE)
    except Exception as e:
        send_notification(
            subject="⚠️ APEXIS Script Failed",
            body=f"Failed to save image to database: {e}"
        )
        logger.error(f"Failed to save image to database: {e}")
        exit(1)

    # generate word and save to database
    dict_data = generate_word()
    word_otd = parse_word_data(dict_data)

    if word_otd['word'] == 'default':
        send_notification(
            subject="⚠️ APEXIS Script Warning",
            body="Could not generate a valid word today, using default."
        )

    # save image to database — creates table if it doesn't exist
    try:
        inserted_word = word_to_table(word_otd, WORDS_TABLE)
    except Exception as e:
        send_notification(
            subject="⚠️ APEXIS Script Failed",
            body=f"Failed to save word to database: {e}"
        )
        logger.error(f"Failed to save word to database: {e}")
        exit(1)


    # success notification
    if inserted_word and inserted_img:
        send_notification(
            subject="🌌 APEXIS — Today's content is ready",
            body=f"Image: {img_otd['title']}\nType: {img_otd['media_type']}\n\nWord: {word_otd['word']}\nDefinition: {word_otd['definition']}"
        )
    else:
        logger.info("Skipping notification - Today's content already loaded")


if __name__ == "__main__":
    drop_tables = False
    main(drop_tables)
