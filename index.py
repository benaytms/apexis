"""
Created on Fri Mar 6 23:20:00 2026

@author: benaytms
"""
import requests as rq
import psycopg2
from dotenv import load_dotenv
from random import randint
from datetime import date
import os

load_dotenv()

NASA_API=str(os.getenv('NASA_API'))
DATABASE_URL=str(os.getenv('DATABASE_URL'))
APOD_URL = "https://api.nasa.gov/planetary/apod?api_key=" + NASA_API
DICT_URL = "https://api.dictionaryapi.dev/api/v2/entries/en"
RANDOMWORD_URL = "https://random-words-api.kushcreates.com/api?language=en"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMGS_DIR = os.path.join(BASE_DIR, "images/")

ALLOWED_TABLES = ("apod_images", "words_dict")

def word_exists(word: str) -> bool:
    """
    Checks if word is already in the Data Base
    """
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM words_dict WHERE word = %s", (word,)
            )
            return cursor.fetchone() is not None

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

def print_table(table_name:str, limit:int=10) -> None:
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

def download_img(image_data:dict):
    """
    Downloads the current image.
    """
    image_url = image_data['url']
    date = image_data['date']
    
    try:
        os.makedirs(IMGS_DIR, exist_ok=True)
    
        filename = f"apod_{date}.jpg"
        filepath = os.path.join(IMGS_DIR, filename)

        try:
            img_response = rq.get(image_url)
        except Exception as e:
            print("Image not available, due to error: ", e)
            return
    
        if img_response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
        
            print(f"image saved: {filepath}")
        else:
            print("An error occurred, the image was not saved, \
            status code:", img_response.status_code)
    
    except Exception as e:
        print("Failed to download image, error: ", e)

def delete_imgs(directory:str) -> None:
    today = date.today().isoformat()
    today_img = str(f"apod_{today}.jpg")
    keep = ["example.jpeg", today_img]
    for filename in os.listdir(directory):
        if filename not in keep:
            os.remove(os.path.join(directory, filename))

def generate_word():
    """
    Generates the random word using the Random Words API, then
    passes this word to the Free Dictionary API to get its definition.

    There is a limit attempts of getting a valid word of 20.
    If none is found, the word 'default' is chosen.
    """
    max_attempts = 200
    
    for attempt in range(max_attempts):
        
        word_response = rq.get(RANDOMWORD_URL)
        
        if word_response.status_code != 200:
            continue
            
        try:
            word_data = word_response.json()
            n = randint(0, len(word_data)-1)
            
            random_word = word_data[n]['word']

            if word_exists(random_word):
                print(f"Word '{random_word}' already in database, trying again...")
                continue
            
            dict_response = rq.get(f"{DICT_URL}/{random_word}")
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

    # If the word is default, something went wrong with the word generation
    return 'default'

def img_to_table(img_otd:dict, table_name:str) -> None:
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

def word_to_table(word_otd:dict, table_name:str) -> None:
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

def main(drop_tables:bool=False) -> None:
    """
    Main code function - Serves to integrate everything into one place.
    """
    IMGS_TABLE = ALLOWED_TABLES[0]
    WORDS_TABLE = ALLOWED_TABLES[1]

    # this works to drop every table, in case it's needed
    if drop_tables:
        drop_table(IMGS_TABLE)
        drop_table(WORDS_TABLE)
        exit(1)

    # makes the get request to the APOD URL
    response = rq.get(APOD_URL)

    # if the response is successful, retrieves the data from the JSON file
    if response.status_code == 200:
        img_data=response.json()
        print("Request successful")
    else:
        print("An error occurred: ", response.status_code)
        exit(1)

    # creates image dictionary with information about the image
    img_otd = { 
        "title": img_data.get('title', 'No title'),
        "date": img_data.get('date', '01-01-0001'),
        "exp": img_data.get('explanation', 'No explanation'),
        "img_url": img_data.get('url', 'No url'),
        "copyr": img_data.get('copyright', 'No copyright'),
        "media_type": img_data.get('media_type', 'image')
    }

    # adds all the information of the image to the image table
    try:
        img_to_table(img_otd, IMGS_TABLE)
    except Exception as e:
        print("Failed to save image to DB, error: ", e)
        exit(1)

    # downloads the image to the images directory
    if img_data.get("media_type") == 'image':
        n_imgs = len(os.listdir(IMGS_DIR))
        if n_imgs > 732:
            delete_imgs(IMGS_DIR)
        download_img(img_data)
    else:
        print("Skipping image download, today's a video!")

    # generates random word for the dictionary, and makes sure the word isn't already on the Data Base
    dict_data = generate_word()

    if dict_data=='default':
        word_otd = {
            "word": 'default',
            "definition": 'automatic or standard way of acting or responding.'
        }
        print("Could not generate a valid word today, using default. :(")
    else:
        word_otd = {
            "word": dict_data[0].get("word", 'No word'),
            "definition": dict_data[0]['meanings'][0]['definitions'][0].get("definition", 'No definition')
        }
    # adds the word and its definition to the table
    word_to_table(word_otd, WORDS_TABLE)


if __name__ == "__main__":
    action = True      # defines if should reset both tables or not, 0 for normal behavior, 1 for reset
    main(action)

