from pydantic import BaseModel
from typing import Optional

class ImageResponse(BaseModel):
    id: int
    title: str
    date: str
    explanation: str
    url: str
    copyright: str='NASA, ESA, CSA, STScI'
    media_type: str='image'

class WordResponse(BaseModel):
    id: int
    word: str
    definition: str
    date: str
