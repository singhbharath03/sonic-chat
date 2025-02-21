from typing import Any, List, Optional
from uuid import UUID
from pydantic import BaseModel

from django.db import models


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


class SwapTransactionSteps(models.IntegerChoices):
    # States for Swapping token A to token B
    APPROVAL_A = 1
    BUILD_SWAP_TX = 2


class SiloLendingDepositTxnSteps(models.IntegerChoices):
    APPROVAL = 1
    DEPOSIT = 2


class SiloLendingWithdrawTxnSteps(models.IntegerChoices):
    WITHDRAW = 1


class TransactionFlows(models.IntegerChoices):
    SWAP = 0
    SILO_LENDING_DEPOSIT = 1
    SILO_LENDING_WITHDRAW = 2


class TransactionStates(models.IntegerChoices):
    PROCESSING = 0
    COMPLETED = 1
    FAILED = 2
