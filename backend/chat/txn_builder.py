from typing import Dict

from chaindata.evm.constants import ABI
from chaindata.evm.utils import get_w3
from chaindata.evm.token_lists import get_token_addresses_from_symbols
from chaindata.constants import SONIC_NATIVE_TOKEN_PLACEHOLDER_ADDRESS, IntChainId
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


async def check_and_build_allowance(
    token_address: str,
    user_address: str,
    spender_address: str,
    amount: float,
    token_decimals: int,
    token_symbol: str,
) -> Dict | None:
    """Check allowance and build approval transaction if needed"""
    if token_address == SONIC_NATIVE_TOKEN_PLACEHOLDER_ADDRESS:
        return None

    w3 = await get_w3(IntChainId.Sonic)
    contract = w3.eth.contract(address=token_address, abi=ABI.ERC20)
    allowance = await contract.functions.allowance(user_address, spender_address).call()

    if allowance < amount * 10**token_decimals:
        return await build_allowance_transaction(
            IntChainId.Sonic,
            user_address,
            token_address,
            spender_address,
            token_symbol,
        )
    return None


async def build_allowance_transaction(
    chain_id: IntChainId,
    user_address: str,
    token_address: str,
    spender_address: str,
    token_symbol: str,
) -> Dict:
    w3 = await get_w3(chain_id)
    contract = w3.eth.contract(address=token_address, abi=ABI.ERC20)
    txn = await contract.functions.approve(
        spender_address, 2**256 - 1
    ).build_transaction({"from": user_address})

    return {
        "transaction": txn,
        "description": f"Approving {spender_address} to spend {token_symbol} for lending",
    }
