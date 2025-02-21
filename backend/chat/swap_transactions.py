from typing import Dict
import logging

from chat.txn_builder import build_transaction_request, check_and_build_allowance
from chaindata.evm.token_lists import get_token_addresses_from_symbols
from chaindata.evm.utils import get_w3
from chaindata.evm.constants import ABI
from chaindata.odos import build_swap_transaction
from chaindata.evm.token_metadata import get_token_metadata
from chat.models import Conversation, TransactionRequests
from chat.typing import SwapTransactionSteps, TransactionFlows, TransactionStates
from chaindata.constants import (
    ODOS_ROUTER_SPENDER_ADDRESS,
    SONIC_NATIVE_TOKEN_PLACEHOLDER_ADDRESS,
    IntChainId,
)
from chat.txn_builder import validate_token


logger = logging.getLogger(__name__)


async def swap_tokens(
    conversation: Conversation,
    user_address: str,
    input_token_symbol: str,
    input_token_amount: float,
    output_token_symbol: str,
) -> dict:
    # Called when LLM requests a swap
    transaction_request = await build_transaction_request(
        conversation,
        user_address,
        TransactionFlows.SWAP,
        {
            "input_token_symbol": input_token_symbol,
            "input_token_amount": input_token_amount,
            "output_token_symbol": output_token_symbol,
        },
    )

    input_token_address, error = await validate_token(
        input_token_symbol, transaction_request
    )
    if error:
        return f"Error: {error}"

    output_token_address, error = await validate_token(
        output_token_symbol, transaction_request
    )
    if error:
        return f"Error: {error}"

    data = transaction_request.data
    data.update(
        {
            "input_token_address": input_token_address,
            "output_token_address": output_token_address,
        }
    )
    transaction_request.data = data
    await transaction_request.asave()

    return await process_swap_transaction(transaction_request)


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

    transaction_details = await check_and_build_allowance(
        input_token_address,
        user_address,
        ODOS_ROUTER_SPENDER_ADDRESS,
        input_token_amount,
        input_token_decimals,
        input_token_symbol,
    )

    if transaction_details:
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
        f"Swapping {input_token_amount} {input_token_symbol} to {output_token_symbol}"
    )

    transaction_request.transaction_details = transaction_details
    await transaction_request.asave()
    return True
