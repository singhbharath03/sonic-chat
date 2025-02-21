import asyncio

from tools.dictionary import get_from_dict
from tools.http import req_post
from chat.txn_builder import (
    build_transaction_request,
    check_and_build_allowance,
    validate_token,
)
from chaindata.evm.utils import get_w3
from chaindata.evm.constants import ABI
from chaindata.evm.token_metadata import get_token_metadata
from chat.models import Conversation, TransactionRequests
from chat.typing import SiloLendingDepositTxnSteps, TransactionFlows
from chaindata.constants import IntChainId
import logging

logger = logging.getLogger(__name__)


async def lend_tokens(
    conversation: Conversation,
    user_address: str,
    token_symbol: str,
    amount: float,
) -> bool:
    transaction_request = await build_transaction_request(
        conversation,
        user_address,
        TransactionFlows.LEND,
        {
            "token_symbol": token_symbol,
            "amount": amount,
        },
    )

    token_address, error = await validate_token(token_symbol, transaction_request)
    if error:
        return error

    data = transaction_request.data
    data.update({"token_address": token_address})
    transaction_request.data = data
    await transaction_request.asave()

    return await process_lend_transaction(transaction_request)


async def process_lend_transaction(transaction_request: TransactionRequests) -> bool:
    """Process the lending transaction and returns a bool indicating if transaction signing is required"""

    token_symbol = transaction_request.data.get("token_symbol")
    token_address = transaction_request.data.get("token_address")
    amount = transaction_request.data.get("amount")
    user_address = transaction_request.user_address

    token_metadata = await get_token_metadata([token_address])
    if metadata := token_metadata.get(token_address):
        token_decimals = metadata.decimals
    else:
        logger.warning(f"Token {token_address} not found in token metadata")
        token_decimals = 18

    lending_vault = await get_best_lending_vault(token_address)
    if lending_vault is None:
        return False

    if transaction_request.step < SiloLendingDepositTxnSteps.APPROVAL:
        needs_txn_signing = await handle_approval_step(
            transaction_request,
            lending_vault,
            token_address,
            token_symbol,
            user_address,
            amount,
            token_decimals,
        )
        if needs_txn_signing:
            return True

    if transaction_request.step < SiloLendingDepositTxnSteps.LEND:
        needs_txn_signing = await handle_lend_step(
            transaction_request,
            lending_vault,
            token_address,
            amount,
            token_symbol,
            token_decimals,
            user_address,
        )
        if needs_txn_signing:
            return True

    return False


async def handle_approval_step(
    transaction_request: TransactionRequests,
    lending_vault: str,
    token_address: str,
    token_symbol: str,
    user_address: str,
    amount: float,
    token_decimals: int,
) -> bool:
    """Handles the approval step of the lending transaction"""
    transaction_request.step = SiloLendingDepositTxnSteps.APPROVAL

    transaction_details = await check_and_build_allowance(
        token_address,
        user_address,
        lending_vault,
        amount,
        token_decimals,
        token_symbol,
    )

    if transaction_details:
        transaction_request.transaction_details = transaction_details
        await transaction_request.asave()
        return True

    await transaction_request.asave()
    return False


async def handle_lend_step(
    transaction_request: TransactionRequests,
    lending_vault: str,
    token_address: str,
    amount: float,
    token_symbol: str,
    token_decimals: int,
    user_address: str,
) -> bool:
    """Handles the lending step of the transaction"""
    transaction_request.step = SiloLendingDepositTxnSteps.LEND

    w3 = await get_w3(IntChainId.Sonic)
    contract = w3.eth.contract(address=lending_vault, abi=ABI.SILO)

    amount_in_wei = int(amount * 10**token_decimals)

    txn = await contract.functions.deposit(
        amount_in_wei, token_address
    ).build_transaction({"from": user_address})

    transaction_details = {
        "transaction": txn,
        "description": f"Lend {amount} {token_symbol} to Silo Protocol",
    }

    transaction_request.transaction_details = transaction_details
    await transaction_request.asave()
    return True


async def get_silo_markets():
    return await req_post(
        "https://v2.silo.finance/api/display-markets-v2",
        {
            "isApeMode": False,
            "isCurated": True,
            "protocolKey": None,
            "search": None,
            "sort": None,
        },
    )


async def get_best_lending_vault(token_address: str):
    markets = await get_silo_markets()

    config_address = None
    best_apy = 0
    for market in markets:
        for silo_key in ["silo0", "silo1"]:
            if get_from_dict(market, [silo_key, "tokenAddress"]) == token_address:
                silo_details = get_from_dict(market, [silo_key])

                # Convert base APR to float
                total_apy = float(silo_details["collateralBaseApr"]) / pow(10, 16)
                for collateral_program in silo_details["collateralPrograms"]:
                    # Convert program APR to float and add
                    total_apy += float(collateral_program["apr"]) / pow(10, 16)

                if total_apy > best_apy:
                    best_apy = total_apy
                    config_address = market["configAddress"]

    if config_address is not None:
        w3 = await get_w3(IntChainId.Sonic)
        silo_vaults = await (
            w3.eth.contract(address=config_address, abi=ABI.SILO_CONFIG)
            .functions.getSilos()
            .call()
        )

        # Get all asset addresses concurrently
        asset_addresses = await asyncio.gather(
            *[
                w3.eth.contract(address=vault, abi=ABI.SILO).functions.asset().call()
                for vault in silo_vaults
            ]
        )

        # Find matching vault
        for vault, asset in zip(silo_vaults, asset_addresses):
            if asset == token_address:
                return vault

    return None
