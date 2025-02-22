import uuid

from django.db import models

from tools.app_model import AppModel
from chaindata.constants import IntChainId
from chat.typing import SwapTransactionSteps, TransactionFlows, TransactionStates


class Conversation(AppModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255)
    messages = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id}"


class TransactionRequests(AppModel):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.DO_NOTHING, related_name="transaction_requests"
    )
    chain_id = models.PositiveSmallIntegerField(choices=IntChainId.choices, null=False)
    """
    For swaps has data like input_token_address, output_token_address, amount
    """
    user_address = models.CharField(max_length=255)
    flow = models.PositiveSmallIntegerField(
        choices=TransactionFlows.choices,
        null=False,
        default=TransactionFlows.SWAP,
    )
    data = models.JSONField()
    state = models.PositiveSmallIntegerField(
        choices=TransactionStates.choices,
        null=False,
        default=TransactionStates.PROCESSING,
    )
    step = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    failed_reason = models.CharField(max_length=255, null=True)
    transaction_details = models.JSONField(null=True)
    tool_call_id = models.CharField(max_length=255, null=True)
    signed_tx_hash = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f"TransactionRequest {self.id}"
