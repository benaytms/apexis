"""
Created on Fri Mar 6 23:20:00 2026

@author: benaytms
"""
import requests as rq
import sqlite3 as sql3
from dotenv import load_dotenv
from random import randint
import os

load_dotenv()

NASA_API=os.getenv('NASA_API')
DB_NAME = "apod_words.db"
URL = "https://api.nasa.gov/planetary/apod?api_key=" + str(NASA_API)
DICT_URL = "https://api.dictionaryapi.dev/api/v2/entries/en"
RANDOMWORD_URL = "https://random-words-api.kushcreates.com/api?language=en"
IMGS_DIR = "images/"

ALLOWED_TABLES = ("apod_images", "words_dict")

def drop_table(table_name:str) -> None:
    """
    Drops table from Data Base.
    """

    try:
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Unknown table: '{table_name}'")

        with sql3.connect(DB_NAME) as conn:
            conn.execute(f"DROP TABLE {table_name};")
            print(f"Table {table_name} dropped.")
        
    except Exception as e:
        print("An error occurred: ", e)

def print_table(table_name:str, limit:int=10) -> None:
    """
    Prints off specified table. The purpose of this function
    is to check if the data on the Data Base is correctly stored.

    Fetchall method causes memory overload on long tables, fetchmany
    is used instead, which needs a limit of rows to be specified, the default is 10.
    """
    try:
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Unknown table: '{table_name}'")

        with sql3.connect(DB_NAME) as conn:
            rows = conn.execute(f"SELECT * FROM {table_name}").fetchmany(limit)
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
        os.makedirs('images', exist_ok=True)
    
        filename = f"apod_{date}.jpg"
        filepath = os.path.join('images/', filename)

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

def generate_word():
    """
    Generates the random word using the Random Words API, then
    passes this word to the Free Dictionary API to get its definition.

    There is a limit attempts of getting a valid word of 20.
    If none is found, the word 'default' is chosen.
    """
    max_attempts = 20
    
    for attempt in range(max_attempts):
        
        word_response = rq.get(RANDOMWORD_URL)
        
        if word_response.status_code != 200:
            continue
            
        try:
            word_data = word_response.json()
            n = randint(0, len(word_data)-1)
            
            random_word = word_data[n]['word']
            
            dict_response = rq.get(f"{DICT_URL}/{random_word}")
            dict_data = dict_response.json()
            
            if isinstance(dict_data, list):
                print(f"Found valid word: {random_word}")
                return dict_data
            else:
                print(f"Word '{random_word}' not in dictionary, trying again...")
                continue
                
        except Exception as e:
            print("Error:", e)
            continue

    # If the word is default, something went wrong with the word generation
    return 'default'

def img_to_table(img_otd:dict, table_name:str) -> None:
    """
    Insert APOD information to the images table
    from the apod_words Data Base.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Unknown table: '{table_name}'")

    with sql3.connect(DB_NAME) as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY,
                    title TEXT UNIQUE NOT NULL,
                    date TEXT UNIQUE NOT NULL,
                    explanation TEXT NOT NULL,
                    url TEXT NOT NULL,
                    copyright TEXT
                )
            ''')

            cursor.execute(f'''
                INSERT OR IGNORE INTO {table_name} 
                    (title, date, explanation, url, copyright)
                VALUES 
                    (?, ?, ?, ?, ?)
                ''',
                (img_otd['title'], img_otd['date'], 
                 img_otd['exp'], img_otd['img_url'], 
                 img_otd['copyr'])
                )

        except Exception as e:
            print("Error: ", e)

def word_to_table(word_otd:dict, table_name:str) -> None:
    """
    Insert Word information to the words table
    from the apod_words Data Base.
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Unknown table: '{table_name}'")

    with sql3.connect(DB_NAME) as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY,
                word TEXT UNIQUE NOT NULL,
                definition TEXT NOT NULL
                )
            ''')

            cursor.execute(f'''
                INSERT OR IGNORE INTO {table_name}
                (word, definition)
                VALUES 
                (?, ?)
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

    if drop_tables==True:
        drop_table(IMGS_TABLE)
        drop_table(WORDS_TABLE)
        exit(1)

    response = rq.get(URL)

    if response.status_code == 200:
        img_data=response.json()
        print("Request successful")
    else:
        print("An error occurred: ", response.status_code)
        exit(1)


    img_otd = { 
        "title": img_data.get('title', 'No title'),
        "date": img_data.get('date', '01-01-0001'),
        "exp": img_data.get('explanation', 'No explanation'),
        "img_url": img_data.get('url', 'No url'),
        "copyr": img_data.get('copyright', 'No copyright')
    }

    img_to_table(img_otd, IMGS_TABLE)
    download_img(img_data)


    dict_data = generate_word()
    if dict_data=='default':
        word_otd = {
            "word": 'default',
            "definition": 'automatic or standard way of acting or responding.'
        }
    else:
        word_otd = {
            "word": dict_data[0].get("word", 'No word'),
            "definition": dict_data[0]['meanings'][0]['definitions'][0].get("definition", 'No definition')
        }
        
    word_to_table(word_otd, WORDS_TABLE)


if __name__ == "__main__":
    action = False      # defines if should reset both tables or not, 0 for normal behavior, 1 for reset
    main(action)

