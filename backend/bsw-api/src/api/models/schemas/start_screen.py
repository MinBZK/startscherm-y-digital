from pydantic import BaseModel
from typing import List


class Document(BaseModel):
    id: str
    title: str


class Task(BaseModel):
    id: str
    description: str


class CalendarEvent(BaseModel):
    id: str
    summary: str


class NewsItem(BaseModel):
    id: str
    headline: str


class Message(BaseModel):
    id: str
    from_: str
    subject: str


class StartScreenResponse(BaseModel):
    documents: List[Document]
    tasks: List[Task]
    calendar: List[CalendarEvent]
    news: List[NewsItem]
    messages: List[Message]
