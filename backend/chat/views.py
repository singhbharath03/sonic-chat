import logging
from typing import List, Optional

from chaindata.evm.typing import TokenHoldings
from chaindata.evm.token_balances import TokenHolding, get_sonic_token_holdings
from chat.models import Conversation
from tools.privy import get_user_profile
from chat.typing import (
    ChatResponse_,
    ConversationResponse_,
    Message_,
    ProcessMessageRequest_,
    SubmitTransactionRequest_,
)
from chat.llm_conversation import (
    NEW_THREAD_START_MESSAGES,
    complete_conversation,
    submit_signed_transaction,
)
from fastapi import APIRouter, Request, HTTPException


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/process_messages/")
async def process_message(
    request: ProcessMessageRequest_, privy_user_id: str
) -> ConversationResponse_:
    # Get conversation, add new message and save
    conversation = await Conversation.objects.aget(id=request.id)
    conversation.messages.append({"role": "user", "content": request.user_message})
    await conversation.asave()

    user_details = await get_user_profile(privy_user_id)
    needs_txn_signing = await complete_conversation(conversation, user_details)

    return ConversationResponse_(
        id=conversation.id,
        messages=conversation.messages,
        needs_txn_signing=needs_txn_signing,
    )


@router.get("/new_thread/", response_model=ConversationResponse_)
async def new_thread(request: Request, privy_user_id: str) -> ConversationResponse_:
    conversation = await Conversation.objects.acreate(
        user_id=privy_user_id, messages=NEW_THREAD_START_MESSAGES
    )

    return ConversationResponse_(id=conversation.id, messages=conversation.messages)


@router.get(
    "/conversations/{conversation_id}/pending_transaction",
)
async def get_pending_transaction(request: Request, conversation_id: str):
    """Get pending transaction for a conversation"""
    try:
        conversation = await Conversation.objects.aget(id=conversation_id)
    except Conversation.DoesNotExist:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not conversation.pending_transaction:
        raise HTTPException(status_code=404, detail="No pending transaction found")

    return {"transaction_details": conversation.pending_transaction}


@router.post(
    "/conversations/{conversation_id}/submit_transaction",
)
async def submit_transaction(
    request: SubmitTransactionRequest_, conversation_id: str
) -> ConversationResponse_:
    """Submit a signed transaction hash and continue the conversation"""
    try:
        conversation = await Conversation.objects.aget(id=conversation_id)
    except Conversation.DoesNotExist:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await submit_signed_transaction(conversation, request.signed_tx_hash)

    return ConversationResponse_(
        id=conversation.id,
        messages=conversation.messages,
        needs_txn_signing=False,
    )


@router.get(
    "/sonic_holdings",
)
async def get_sonic_holdings(request: Request, privy_user_id: str) -> TokenHoldings:
    user_details = await get_user_profile(privy_user_id)

    return await get_sonic_token_holdings(user_details.evm_wallet_address)
