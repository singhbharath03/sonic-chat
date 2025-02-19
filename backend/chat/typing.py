from typing import List, Optional

from pydantic import BaseModel


class Message_(BaseModel):
    role: str
    content: Optional[str] = None


class ChatResponse_(BaseModel):
    messages: List[Message_]


class ProcessMessageRequest_(BaseModel):
    messages: List[Message_]
