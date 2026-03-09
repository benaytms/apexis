from pydantic import BaseModel

class ImageResponse(BaseModel):
    id: int
    title: str
    date: str
    explanation: str
    url: str
    copyright: str
    media_type: str

class WordResponse(BaseModel):
    id: int
    word: str
    definition: str
    date: str
