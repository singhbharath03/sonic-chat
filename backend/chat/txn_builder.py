from typing import Dict

from chaindata.evm.token_lists import get_token_addresses_from_symbols
from chaindata.constants import IntChainId
from chat.models import Conversation, TransactionRequests
from chat.typing import TransactionFlows, TransactionStates


async def build_transaction_request(
    conversation: Conversation,
    user_address: str,
    flow: TransactionFlows,
    data: Dict,
) -> TransactionRequests:
    """Helper to create or get existing transaction request"""
    try:
        transaction_request = await TransactionRequests.objects.aget(
            conversation=conversation, state=TransactionStates.PROCESSING
        )
        assert transaction_request.flow == flow
    except TransactionRequests.DoesNotExist:
        transaction_request = await TransactionRequests.objects.acreate(
            chain_id=IntChainId.Sonic,
            conversation=conversation,
            user_address=user_address,
            flow=flow,
            data=data,
        )
    return transaction_request


async def validate_token(
    token_symbol: str,
    transaction_request: TransactionRequests,
) -> tuple[str | None, str | None]:
    """Validate token and return (token_address, error_message)"""
    token_address_by_symbol = await get_token_addresses_from_symbols([token_symbol])
    token_address = token_address_by_symbol.get(token_symbol)

    if token_address is None:
        error = f"Token {token_symbol} not supported"
        transaction_request.failed_reason = error
        transaction_request.state = TransactionStates.FAILED
        await transaction_request.asave()
        return None, error

    return token_address, None
