import logging
from typing import List, Optional

from chaindata.evm.typing import TokenHoldings
from chaindata.evm.token_balances import TokenHolding, get_sonic_token_holdings
from chat.models import Conversation, TransactionRequests
from tools.privy import get_user_profile
from chat.typing import (
    ChatResponse_,
    ConversationResponse_,
    MessageDetails_,
    ProcessMessageRequest_,
    SubmitTransactionRequest_,
    TransactionStates,
)
from chat.llm_conversation import (
    SYSTEM_PROMPT,
    complete_conversation,
    is_user_wallet_funded,
    submit_signed_transaction,
)
from fastapi import APIRouter, Request, HTTPException


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/process_messages")
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
        messages=await build_message_details(conversation),
        needs_txn_signing=needs_txn_signing,
    )


@router.get("/new_thread", response_model=ConversationResponse_)
async def new_thread(request: Request, privy_user_id: str) -> ConversationResponse_:
    user_details = await get_user_profile(privy_user_id)
    is_wallet_funded = await is_user_wallet_funded(user_details)
    if not is_wallet_funded:
        assistant_message = "Hello! I'm here to help you get started on Sonic Chain. Let's get you set up. Please fund your wallet with natives on Base or Sonic chain."
    else:
        assistant_message = "Hello! I'm here to help you explore Sonic Chain."

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "assistant",
            "content": assistant_message,
        },
    ]
    conversation = await Conversation.objects.acreate(
        user_id=privy_user_id, messages=messages
    )

    return ConversationResponse_(
        id=conversation.id, messages=await build_message_details(conversation)
    )


@router.get(
    "/conversations/{conversation_id}/pending_transaction",
)
async def get_pending_transaction(request: Request, conversation_id: str):
    """Get pending transaction for a conversation"""
    try:
        conversation = await Conversation.objects.aget(id=conversation_id)
    except Conversation.DoesNotExist:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        transaction_request = await TransactionRequests.objects.aget(
            conversation=conversation, state=TransactionStates.PROCESSING
        )
    except TransactionRequests.DoesNotExist:
        raise HTTPException(
            status_code=404, detail="No pending transaction found for conversation"
        )
    except TransactionRequests.MultipleObjectsReturned:
        raise HTTPException(
            status_code=409,
            detail="Multiple pending transactions found for conversation",
        )

    return {"transaction_details": transaction_request.transaction_details}


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

    needs_txn_signing = await submit_signed_transaction(
        conversation, request.signed_tx_hash
    )

    return ConversationResponse_(
        id=conversation.id,
        messages=await build_message_details(conversation),
        needs_txn_signing=needs_txn_signing,
    )


@router.get(
    "/sonic_holdings",
)
async def get_sonic_holdings(request: Request, privy_user_id: str) -> TokenHoldings:
    user_details = await get_user_profile(privy_user_id)

    return await get_sonic_token_holdings(user_details.evm_wallet_address)


async def build_message_details(conversation: Conversation) -> List[MessageDetails_]:
    """
    Transaction requests stores signed txn hash and tool call id. The first assistant message after tool call request should have the txn hash.
    """
    signed_txn_hash_by_tool_call_id = {}
    async for transaction_request in TransactionRequests.objects.filter(
        conversation=conversation, state=TransactionStates.COMPLETED
    ):
        signed_txn_hash_by_tool_call_id[transaction_request.tool_call_id] = (
            transaction_request.signed_tx_hash
        )

    tool_call_id = None
    message_details = []
    for message in conversation.messages:
        current_tx_hash = None

        if message.get("tool_calls"):
            tool_call_id = message["tool_calls"][0]["id"]
        elif tool_call_id and message["role"] == "assistant":
            current_tx_hash = signed_txn_hash_by_tool_call_id.get(tool_call_id)
            tool_call_id = None  # Reset after using it

        message_details.append(
            MessageDetails_(
                role=message["role"],
                content=message.get("content"),
                tx_hash=current_tx_hash,
            )
        )

    return message_details
