"""
Created on Fri Mar 6 23:20:00 2026

@author: benaytms
"""
import requests as rq
import psycopg2
from dotenv import load_dotenv
from random import randint
import os

load_dotenv()

NASA_API = str(os.getenv('NASA_API'))
DATABASE_URL = str(os.getenv('DATABASE_URL'))
DISCORD_WEBHOOK = str(os.getenv('DISCORD_WEBHOOK'))

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
            print("Notification sent!")
        else:
            print(f"Notification failed: {response.status_code}")
    except Exception as e:
        print("Failed to send notification", e)
        


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
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                print(f"Table {table_name} dropped.")

    except Exception as e:
        print("An error occurred: ", e)


def print_table(table_name:str, limit:int = 10) -> None:
    """
    Prints off specified table for debugging purposes.
    """
    try:
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Unknown table: '{table_name}'")

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
                rows = cursor.fetchall()
                print(f"Table {table_name}:")
                for row in rows:
                    print(row)

    except Exception as e:
        print("An error occurred: ", e)


def generate_word():
    """
    Generates a random word using the Random Words API, then
    passes it to the Free Dictionary API to get its definition.
    Skips words already in the database.
    Limit of 120 attempts before falling back to 'default'.
    """
    max_attempts = 120

    for attempt in range(max_attempts):

        word_response = rq.get(RANDOMWORD_URL, timeout=10)

        if word_response.status_code != 200:
            continue

        try:
            word_data = word_response.json()
            n = randint(0, len(word_data) - 1)
            random_word = word_data[n]['word']

            if word_exists(random_word):
                print(f"Word '{random_word}' already in database, trying again...")
                continue

            dict_response = rq.get(f"{DICT_URL}/{random_word}", timeout=10)
            dict_data = dict_response.json()

            if isinstance(dict_data, list):
                print(f"Found valid word: {random_word}")
                return dict_data
            else:
                print(f"Word '{random_word}' not available, trying again...")
                continue

        except Exception as e:
            print("Error:", e)
            continue

    return 'default'


def img_to_table(img_otd:dict, table_name:str) -> None:
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
                        copyright TEXT,
                        media_type TEXT NOT NULL DEFAULT 'image'
                    )
                ''')

                cursor.execute(f'''
                    INSERT INTO {table_name}
                        (title, date, explanation, url, copyright, media_type)
                    VALUES
                        (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    ''',
                    (img_otd['title'], img_otd['date'],
                     img_otd['exp'], img_otd['img_url'],
                     img_otd['copyr'], img_otd['media_type'])
                )

            except Exception as e:
                print("Error: ", e)
                raise


def word_to_table(word_otd:dict, table_name:str) -> None:
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
                        definition TEXT NOT NULL
                    )
                ''')

                cursor.execute(f'''
                    INSERT INTO {table_name}
                        (word, definition)
                    VALUES
                        (%s, %s)
                    ON CONFLICT DO NOTHING
                    ''',
                    (word_otd['word'], word_otd['definition'])
                )

            except Exception as e:
                print("Error: ", e)
                raise


def main(drop_tables:bool = False) -> None:
    """
    Main function — integrates everything into one place.
    """
    IMGS_TABLE = ALLOWED_TABLES[0]
    WORDS_TABLE = ALLOWED_TABLES[1]

    # drop tables if requested
    if drop_tables:
        drop_table(IMGS_TABLE)
        drop_table(WORDS_TABLE)
        print('All tables dropped!')
        exit(1)

    # fetch NASA APOD
    response = rq.get(APOD_URL, timeout=10)

    if response.status_code == 200:
        img_data = response.json()
        print("Request successful")
    else:
        print("An error occurred: ", response.status_code)
        send_notification(
            subject="⚠️ APEXIS Script Failed",
            body="NASA API request failed."
        )
        exit(1)

    # build image dict
    img_otd = {
        "title": img_data.get('title', 'No title'),
        "date": img_data.get('date', '01-01-0001'),
        "exp": img_data.get('explanation', 'No explanation'),
        "img_url": img_data.get('url', 'No url'),
        "copyr": img_data.get('copyright', 'No copyright'),
        "media_type": img_data.get('media_type', 'image')
    }

    # save image to database — creates table if it doesn't exist
    try:
        img_to_table(img_otd, IMGS_TABLE)
    except Exception as e:
        print("Failed to save image to DB:", e)
        send_notification(
            subject="⚠️ APEXIS Script Failed",
            body=f"Failed to save image to database: {e}")
        exit(1)


    # generate word and save to database
    dict_data = generate_word()

    if dict_data == 'default':
        word_otd = {
            "word": 'default',
            "definition": 'automatic or standard way of acting or responding.'
        }
        print("Could not generate a valid word today, using default. :(")
        send_notification(
            subject="⚠️ APEXIS Script Warning",
            body="Could not generate a valid word today, using default.")
    else:
        word = dict_data[0].get("word")

        # put together all definitions in one string
        meanings=dict_data[0]['meanings']
        definitions = []
        for meaning in meanings:
            for definition in meaning['definitions']:
                definitions.append(definition['definition'])
        definitions = definitions[0:3]
        definitions_result = "; ".join(definitions).rstrip('.')
        
        word_otd = {
            "word": word,
            "definition": definitions_result
        }

    word_to_table(word_otd, WORDS_TABLE)

    # success notification
    send_notification(
        subject="🌌 APEXIS — Today's content is ready",
        body=f"Image: {img_otd['title']}\nType: {img_otd['media_type']}\n\nWord: {word_otd['word']}\nDefinition: {word_otd['definition']}"
    )


if __name__ == "__main__":
    action = False  # set to True to reset all tables
    main(action)
