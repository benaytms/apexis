from fastapi import FastAPI, HTTPException
from backend.models import ImageResponse, WordResponse
import backend.database as db

app = FastAPI(title="APOD & Word of the Day API")

@app.get("/image/today", response_model=ImageResponse)
def get_today_image():
    image = db.get_today_image()
    if image is None:
        raise HTTPException(status_code=404, detail="No image for today yet")
    return image

@app.get("/word/today", response_model=WordResponse)
def get_today_word():
    word = db.get_today_word()
    if word is None:
        raise HTTPException(status_code=404, detail="No word for today yet")
    return word