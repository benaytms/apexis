from fastapi import FastAPI, HTTPException, Request
from backend.models import ImageResponse, WordResponse
import backend.database as db
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Slowapi added to avoid extreme rates on FastAPI

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="APOD & Word of the Day API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/image/today", response_model=ImageResponse)
@limiter.limit("30/minute")
def get_today_image(request: Request):
    image = db.get_today_image()
    if image is None:
        raise HTTPException(status_code=404, detail="No image for today yet")
    return image

@app.get("/word/today", response_model=WordResponse)
@limiter.limit("30/minute")
def get_today_word(request: Request):
    word = db.get_today_word()
    if word is None:
        raise HTTPException(status_code=404, detail="No word for today yet")
    return word
