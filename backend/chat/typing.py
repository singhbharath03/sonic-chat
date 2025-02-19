from typing import List

from pydantic import BaseModel


class Message_(BaseModel):
    role: str
    content: str


class ChatResponse_(BaseModel):
    messages: List[Message_]


class ProcessMessageRequest_(BaseModel):
    messages: List[Message_]
