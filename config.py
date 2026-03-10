from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
import os

load_dotenv()

NASA_API = str(os.getenv('NASA_API'))
DATABASE_URL = str(os.getenv('DATABASE_URL'))
DISCORD_WEBHOOK = str(os.getenv('DISCORD_WEBHOOK'))
MERRIAM_KEY = str(os.getenv('MERRIAM_KEY'))
APOD_URL = "https://api.nasa.gov/planetary/apod?api_key=" + NASA_API

def get_today()->str:
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()

