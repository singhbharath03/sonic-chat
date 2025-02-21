from typing import Dict

from chaindata.evm.utils import get_w3
from chaindata.evm.constants import ABI
from chaindata.odos import build_swap_transaction
from chaindata.evm.token_metadata import get_token_metadata
from chat.models import TransactionRequests
from chat.typing import SwapTransactionSteps
from chaindata.constants import ODOS_ROUTER_SPENDER_ADDRESS, IntChainId
import logging

logger = logging.getLogger(__name__)


async def process_swap_transaction(transaction_request: TransactionRequests) -> bool:
    """Process the swap transaction and returns a bool indicating if the transaction signing is required"""

    input_token_symbol = transaction_request.data.get("input_token_symbol")
    output_token_symbol = transaction_request.data.get("output_token_symbol")
    input_token_address = transaction_request.data.get("input_token_address")
    output_token_address = transaction_request.data.get("output_token_address")
    input_token_amount = transaction_request.data.get("input_token_amount")
    user_address = transaction_request.user_address

    token_metadata = await get_token_metadata([input_token_address])
    if metadata := token_metadata.get(input_token_address):
        input_token_decimals = metadata.decimals
    else:
        logger.warning(f"Token {input_token_address} not found in token metadata")
        input_token_decimals = 18

    if transaction_request.step < SwapTransactionSteps.APPROVAL_A:
        needs_txn_signing = await handle_approval_step(
            transaction_request,
            input_token_address,
            input_token_symbol,
            output_token_address,
            user_address,
            input_token_amount,
            input_token_decimals,
        )
        if needs_txn_signing:
            return True

    if transaction_request.step < SwapTransactionSteps.BUILD_SWAP_TX:
        needs_txn_signing = await handle_swap_step(
            transaction_request,
            input_token_address,
            input_token_amount,
            output_token_address,
            input_token_symbol,
            output_token_symbol,
            input_token_decimals,
            user_address,
        )
        if needs_txn_signing:
            return True

    return False


async def handle_approval_step(
    transaction_request: TransactionRequests,
    input_token_address: str,
    input_token_symbol: str,
    output_token_address: str,
    user_address: str,
    input_token_amount: float,
    input_token_decimals: int,
) -> bool:
    """Handles the approval step of the swap transaction and returns a bool indicating if we need to sign the transaction"""
    transaction_request.step = SwapTransactionSteps.APPROVAL_A

    w3 = await get_w3(IntChainId.Sonic)
    contract = w3.eth.contract(address=input_token_address, abi=ABI.ERC20)
    allowance = await contract.functions.allowance(
        user_address, ODOS_ROUTER_SPENDER_ADDRESS
    ).call()

    if allowance < input_token_amount * 10**input_token_decimals:
        transaction_details = await build_allowance_transaction(
            IntChainId.Sonic,
            user_address,
            input_token_address,
            ODOS_ROUTER_SPENDER_ADDRESS,
            input_token_symbol,
        )

        transaction_request.transaction_details = transaction_details
        await transaction_request.asave()
        return True

    await transaction_request.asave()
    return False


async def handle_swap_step(
    transaction_request: TransactionRequests,
    input_token_address: str,
    input_token_amount: float,
    output_token_address: str,
    input_token_symbol: str,
    output_token_symbol: str,
    input_token_decimals: int,
    user_address: str,
) -> bool:
    transaction_request.step = SwapTransactionSteps.BUILD_SWAP_TX

    transaction_details = await build_swap_transaction(
        IntChainId.Sonic,
        input_token_address,
        input_token_amount * 10**input_token_decimals,
        output_token_address,
        user_address,
    )
    transaction_details["description"] = (
        f"Swap {input_token_amount} {input_token_symbol} to {output_token_symbol}"
    )

    transaction_request.transaction_details = transaction_details
    await transaction_request.asave()
    return True


async def build_allowance_transaction(
    chain_id: IntChainId,
    user_address: str,
    token_address: str,
    spender_address: str,
    input_token_symbol: str,
) -> Dict:
    w3 = await get_w3(chain_id)
    contract = w3.eth.contract(address=token_address, abi=ABI.ERC20)
    txn = await contract.functions.approve(
        spender_address, 2**256 - 1
    ).build_transaction({"from": user_address})

    return {
        "transaction": {
            "transaction": txn,  # multiple nesting to keep it same as odos response
        },
        "description": f"Approve {spender_address} to spend {input_token_symbol} for swap",
    }
