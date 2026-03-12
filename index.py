"""
APEXIS - Daily pipeline script

Fetches NASA APOD and a random English word,
stores them in a Postgresql Database, and sends
a Discord notification on completion.

Author: Benay Tomas

Created: 2026-03-06

Last edited: 2026-03-10

Version: 1.0.3
"""

import requests as rq
import psycopg2
import logging
from config import DISCORD_WEBHOOK, DATABASE_URL, APOD_URL
from config import MERRIAM_KEY, get_today
from wonderwords import RandomWord

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s — %(levelname)s — %(message)s'
)

logger = logging.getLogger(__name__)


ALLOWED_TABLES = ("apod_images", "words_dict")


# -------------------------------------------------------- NOTIFICAtIONS ------------------------------------------------- #
############################################################################################################################

def send_notification(subject:str, body:str)->None:
    """
    Sends a Discord notification via webhook.
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
        
############################################################################################################################        
# -------------------------------------------------------- NOTIFICAtIONS ------------------------------------------------- #



# --------------------------------------------- CHECKS IF WORD IS IN THE DATABASE ----------------------------------------- #
############################################################################################################################

def word_exists(word:str)->bool:
    """
    Checks if word is already in the database.
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
        
############################################################################################################################
# --------------------------------------------- CHECKS IF WORD IS IN THE DATABASE ----------------------------------------- #



# ---------------------------------------------------- DROP SPECIFIED TABLE ----------------------------------------------- #
############################################################################################################################

def drop_table(table_name:str)->None:
    """
    Drops table from database.
    """
    try:
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Unknown table: '{table_name}'")

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                logger.warning(f"Table {table_name} dropped.")

    except Exception as e:
        logger.error(f"Could not drop table, error: {e}")
        
#############################################################################################################################
# ----------------------------------------------------- DROP SPECIFIED TABLE ----------------------------------------------- #



# ---------------------------------------------------- PRINT SPECIFIED TABLE ----------------------------------------------- #
#############################################################################################################################

def print_table(table_name:str, limit:int=10)->None:
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
        
############################################################################################################################
# ---------------------------------------------------- PRINT SPECIFIED TABLE ----------------------------------------------- #



# --------------------------------------------------- GENERATES A RANDOM WORD ----------------------------------------------- #
############################################################################################################################

def generate_random_word()->str|None:
    """
    Fetches a single random word.
    Returns the word string or None on failure.
    """
    try:
        r = RandomWord()
        return r.random_words()[0]
    except Exception as e:
        logger.error(f"Could not generate word, error: {e}")
        return None
        
############################################################################################################################
# --------------------------------------------------- GENERATES A RANDOM WORD ---------------------------------------------- #



# --------------------------------------------------- GET DEFINITION OF WORD ----------------------------------------------- #
############################################################################################################################

def get_word_definition(word:str)->dict|None:
    """
    Fetches definition for a given word from Merriam-Webster.
    Returns the first entry dict if valid, None if word has no definition.
    """
    MERRIAM_URL = f"https://www.dictionaryapi.com/api/v3/references/thesaurus/json/{word}?key={MERRIAM_KEY}"

    try:
        response = rq.get(MERRIAM_URL, timeout=5)
        if response.status_code != 200:
            logger.error(f"Merriam API returned {response.status_code}")
            return None

        word_data = response.json()

        # valid response is a list where the first element is a dict
        # if first element is a string or list, word wasn't found
        if isinstance(word_data[0], str) or isinstance(word_data[0], list):
            logger.debug(f"No definition found for '{word}'")
            return None

        return word_data[0]

    except Exception as e:
        logger.error(f"Could not get word definition, error: {e}")
        return None
        
############################################################################################################################
# -------------------------------------------------- GET DEFINITION OF WORD ------------------------------------------------ #



# ----------------------------------------- COORDINATES ALL WORD PROCESSES IN ONE FUNCTION --------------------------------- #
############################################################################################################################

def word_coordinator()->dict:
    """
    Coordinator — generates a random word and fetches its definition.
    Retries until a valid word+definition pair is found or max attempts reached.
    Returns a parsed dict with word, definition, synonyms, and today's date.
    """
    max_attempts = 10

    for attempt in range(1, max_attempts + 1):
        logger.info(f"Word validation, attempt: {attempt}/{max_attempts}")

        word = generate_random_word()
        if not word:
            continue

        if word_exists(word):
            logger.info(f"'{word}' already in database, skipping")
            continue

        definition_data = get_word_definition(word)
        if definition_data is None:
            logger.info(f"'{word}' has no valid definition, skipping")
            continue

        logger.info(f"Found valid word: {word}")
        return parse_word_data(definition_data)

    logger.warning("Max attempts reached, using default word")
    return parse_word_data(None)
    
############################################################################################################################
# ----------------------------------------- COORDINATES ALL WORD PROCESSES IN ONE FUNCTION --------------------------------- #
    


# ---------------------------------------------- GET IMAGE FROM APOD URL ------------------------------------------------- #
############################################################################################################################

def get_image()->dict|None:
    """
    Fetches NASA APOD and returns parsed image dict, or None on failure.
    Retries up to 3 times on server errors before giving up.
    """
    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        logger.info(f"NASA request attempt {attempt}/{max_attempts}")
        try:
            response = rq.get(APOD_URL, timeout=10)
            if response.status_code == 200:
                logger.info("NASA request successful")
                return parse_img_data(response.json())
            elif response.status_code >= 500:
                logger.warning(f"NASA API server error: {response.status_code}, retrying...")
                continue
            else:
                # 4xx errors won't be fixed by retrying (bad key, bad URL, etc.)
                logger.error(f"NASA API client error: {response.status_code}")
                break
        except Exception as e:
            logger.error(f"NASA request failed: {e}")
            continue

    send_notification(
        subject="⚠️ APEXIS Script Failed",
        body="NASA API request failed after all attempts."
    )
    return None
    
############################################################################################################################
# ---------------------------------------------- GET IMAGE FROM APOD URL ------------------------------------------------- #



# ------------------------------------------------- ADD IMAGE TO APOD DATABASE ---------------------------------------------- # ###############################################################################################################################

def img_to_table(img_otd:dict, table_name:str)->bool:
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
                    logger.info("Today's image already in database, skipping.")
                    return False
            except Exception as e:
                logger.error(f"Could not insert image to database, error: {e}")
                raise
                
##############################################################################################################################
# ------------------------------------------------- ADD IMAGE TO APOD DATABASE ------------------------------------------------ #


    
# ----------------------------------------------- ADD WORD TO DICTIONARY DATABASE --------------------------------------------- #
###############################################################################################################################

def word_to_table(word_otd:dict, table_name:str)->bool:
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
                        synonyms TEXT NOT NULL,
                        date TEXT UNIQUE NOT NULL
                    )
                ''')

                cursor.execute(
                    f"SELECT 1 FROM {table_name} WHERE date = %s", (word_otd['date'],)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        f"INSERT INTO {table_name} (word, definition, synonyms, date) VALUES (%s, %s, %s, %s)",
                        (word_otd['word'], word_otd['definition'], word_otd['synonyms'], word_otd['date'])
                    )
                    logger.info(f"Word '{word_otd['word']}' added to database.")
                    return True
                else:
                    logger.info("Today's word already in database, skipping.")
                    return False
            except Exception as e:
                logger.error(f"Failed to insert word to database, error: {e}")
                raise
                
###############################################################################################################################
# ----------------------------------------------- ADD WORD TO DICTIONARY DATABASE --------------------------------------------- #



# ---------------------------------------------------- PARSE IMAGE DATA ------------------------------------------------------- #
###############################################################################################################################

def parse_img_data(img_data:dict)->dict:
    return {
        "title": img_data.get('title', 'No title'),
        "date": img_data.get('date', '01-01-0001'),
        "explanation": img_data.get('explanation', 'No explanation'),
        "url": img_data.get('url', 'No url'),
        "copyright": img_data.get('copyright', 'NASA, ESA, CSA, STScI'),
        "media_type": img_data.get('media_type', 'image')
    }
    
###############################################################################################################################
# ---------------------------------------------------- PARSE IMAGE DATA ------------------------------------------------------- #



# ---------------------------------------------------- PARSE WORD DATA -------------------------------------------------------- #
###############################################################################################################################

def parse_word_data(entry:dict|None)->dict:
    """
    Parses a Merriam-Webster thesaurus entry dict into a flat word dict.
    If entry is None, returns a default fallback word.
    """
    if entry is None:
        logger.warning("Could not generate a valid word today, using default.")
        return {
            "word": "default",
            "definition": "A situation or condition that obtains in the absence of active intervention; absence of choice.",
            "synonyms": "neglect; absence; failure",
            "date": get_today()
        }

    word = entry['hwi']['hw'].capitalize()
    try:
        # def -> sseq -> sense -> dt
        definition = entry['def'][0]['sseq'][0][0][1]['dt'][0][1].capitalize()
        
        syn_list = entry['def'][0]['sseq'][0][0][1]['syn_list'][0][:4]
        syns = '; '.join(i['wd'] for i in syn_list).capitalize()
        
    except (KeyError, IndexError) as e:
        logger.warning(f"Could not parse word entry structure: {e}")
        logger.debug(f"Word structure: {entry}")
        return parse_word_data(None)

    return {
        "word": word,
        "definition": definition,
        "synonyms": syns,
        "date": get_today()
    }
    
###############################################################################################################################
# ---------------------------------------------------- PARSE WORD DATA -------------------------------------------------------- #



# ------------------------------------------------------- MAIN FUNCTION ------------------------------------------------------- #
###############################################################################################################################

def main(drop_tables:bool=False)->None:
    """
    Main function — integrates everything into one place.
    """
    IMGS_TABLE = ALLOWED_TABLES[0]
    WORDS_TABLE = ALLOWED_TABLES[1]
    inserted_img = False
    inserted_word = False

    if drop_tables:
        drop_table(IMGS_TABLE)
        drop_table(WORDS_TABLE)
        logger.warning('All tables dropped!')
        exit(1)

    
    img_otd = get_image()
    if img_otd is None:
        exit(1)
        
    # adds image to table
    try:
        inserted_img = img_to_table(img_otd, IMGS_TABLE)
    except Exception as e:
        send_notification(
            subject="⚠️ APEXIS Script Failed",
            body=f"Failed to save image to database: {e}"
        )
        logger.error(f"Failed to save image to database: {e}")
        exit(1)


    
    word_otd = word_coordinator()
    # adds word to table
    try:
        inserted_word = word_to_table(word_otd, WORDS_TABLE)
    except Exception as e:
        send_notification(
            subject="⚠️ APEXIS Script Failed",
            body=f"Failed to save word to database: {e}"
        )
        logger.error(f"Failed to save word to database: {e}")
        exit(1)

    # if both word and image were inserted correctly, sends notification
    if inserted_word and inserted_img:
        send_notification(
            subject="🌌 APEXIS — Today's content is ready",
            body=f"Image: {img_otd['title']}\nType: {img_otd['media_type']}\n\nWord: {word_otd['word']}\nDefinition: {word_otd['definition']}"
        )
    else:
        logger.info("Skipping notification - Today's content already loaded")
        
################################################################################################################################
# ------------------------------------------------------- MAIN FUNCTION ------------------------------------------------------- #



# --------------------------------------------------------- MAIN CALLER -------------------------------------------------------------- #
###############################################################################################################################

if __name__ == "__main__":
    drop_all_tables = False  # set to True to reset all tables
    main(drop_all_tables)
