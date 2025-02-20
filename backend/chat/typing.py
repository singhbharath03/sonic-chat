from typing import Any, List, Optional
from uuid import UUID
from pydantic import BaseModel


class Message_(BaseModel):
    role: str
    content: Optional[str] = None


class ChatResponse_(BaseModel):
    messages: List[Message_]


class ProcessMessageRequest_(BaseModel):
    id: UUID
    user_message: str


class ConversationResponse_(BaseModel):
    id: UUID
    messages: List[Message_]
    needs_txn_signing: bool = False


class SubmitTransactionRequest_(BaseModel):
    signed_tx_hash: str
