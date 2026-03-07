from pydantic import BaseModel
from typing import Optional

class ImageResponse(BaseModel):
    id: int
    title: str
    date: str
    explanation: str
    url: str
    copyright: Optional[str]=None

class WordResponse(BaseModel):
    id: int
    word: str
    definition: str
