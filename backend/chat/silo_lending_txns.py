import asyncio
from aiocache import cached
from collections import defaultdict

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
from chat.typing import (
    SiloLendingDepositTxnSteps,
    SiloLendingWithdrawTxnSteps,
    TransactionFlows,
)
from chaindata.constants import IntChainId
import logging

logger = logging.getLogger(__name__)


async def withdraw_tokens(
    conversation: Conversation,
    user_address: str,
    token_symbol: str,
    amount: float,
) -> bool:
    transaction_request = await build_transaction_request(
        conversation,
        user_address,
        TransactionFlows.SILO_LENDING_WITHDRAW,
        {"token_symbol": token_symbol, "amount": amount},
    )

    token_address, error = await validate_token(token_symbol, transaction_request)
    if error:
        return error

    data = transaction_request.data
    data.update({"token_address": token_address})
    transaction_request.data = data
    await transaction_request.asave()

    return await process_withdraw_transaction(transaction_request)


async def lend_tokens(
    conversation: Conversation,
    user_address: str,
    token_symbol: str,
    amount: float,
) -> bool:
    transaction_request = await build_transaction_request(
        conversation,
        user_address,
        TransactionFlows.SILO_LENDING_DEPOSIT,
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


async def process_withdraw_transaction(
    transaction_request: TransactionRequests,
) -> bool:
    """Process the withdraw transaction and returns a bool indicating if transaction signing is required"""
    token_address = transaction_request.data.get("token_address")
    amount = transaction_request.data.get("amount")
    token_symbol = transaction_request.data.get("token_symbol")
    user_address = transaction_request.user_address

    token_metadata = await get_token_metadata([token_address])
    if metadata := token_metadata.get(token_address):
        token_decimals = metadata.decimals
    else:
        logger.warning(f"Token {token_address} not found in token metadata")
        token_decimals = 18

    # TODO: load `get_vaults_by_token` on bootup and cache it
    vaults_by_token = await get_vaults_by_token()
    vaults_to_check_for_assets = vaults_by_token.get(token_address) or []

    # Check all vault balances concurrently
    balances = await asyncio.gather(
        *[
            get_user_balance_in_vault(vault, user_address)
            for vault in vaults_to_check_for_assets
        ]
    )

    lending_vault = None
    for vault, balance in zip(vaults_to_check_for_assets, balances):
        if balance > 0:
            lending_vault = vault
            break

    if lending_vault is None:
        return False

    if transaction_request.step < SiloLendingWithdrawTxnSteps.WITHDRAW:
        return await handle_withdraw_step(
            transaction_request,
            lending_vault,
            token_address,
            amount,
            token_symbol,
            token_decimals,
            user_address,
        )

    return False


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

    if transaction_request.step < SiloLendingDepositTxnSteps.DEPOSIT:
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
    transaction_request.step = SiloLendingDepositTxnSteps.DEPOSIT

    w3 = await get_w3(IntChainId.Sonic)
    contract = w3.eth.contract(address=lending_vault, abi=ABI.SILO)

    amount_in_wei = int(amount * 10**token_decimals)

    txn = await contract.functions.deposit(
        amount_in_wei, token_address
    ).build_transaction({"from": user_address})

    transaction_details = {
        "transaction": txn,
        "description": f"Lending {amount} {token_symbol} to Silo Protocol",
    }

    transaction_request.transaction_details = transaction_details
    await transaction_request.asave()
    return True


async def handle_withdraw_step(
    transaction_request: TransactionRequests,
    lending_vault: str,
    token_address: str,
    amount: float,
    token_symbol: str,
    token_decimals: int,
    user_address: str,
) -> bool:
    """Handles the withdraw step of the transaction"""
    transaction_request.step = SiloLendingWithdrawTxnSteps.WITHDRAW

    w3 = await get_w3(IntChainId.Sonic)
    contract = w3.eth.contract(address=lending_vault, abi=ABI.SILO)

    amount_in_wei = int(amount * 10**token_decimals)

    txn = await contract.functions.redeem(
        amount_in_wei, token_address
    ).build_transaction({"from": user_address})

    transaction_details = {
        "transaction": txn,
        "description": f"Withdrawing {amount} {token_symbol} from Silo Protocol",
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
        silo_vaults = await get_silo_vaults(config_address)

        # Get all asset addresses concurrently
        w3 = await get_w3(IntChainId.Sonic)
        asset_addresses = await asyncio.gather(
            *[get_asset_address_from_vault(vault) for vault in silo_vaults]
        )

        # Find matching vault
        for vault, asset in zip(silo_vaults, asset_addresses):
            if asset == token_address:
                return vault

    return None


@cached(ttl=7 * 86400, namespace="silo_vaults")  # 1 week with specific namespace
async def get_vaults_by_token():
    silo_config_addresses = set()
    markets = await get_silo_markets()
    for market in markets:
        silo_config_addresses.add(market["configAddress"])

    resp = await asyncio.gather(
        *[get_silo_vaults(config_address) for config_address in silo_config_addresses]
    )
    all_vault_addresses = set()
    for vault_addresses in resp:
        for vault in vault_addresses:
            all_vault_addresses.add(vault)

    asset_addresses = await asyncio.gather(
        *[get_asset_address_from_vault(vault) for vault in all_vault_addresses]
    )
    vaults_by_token = defaultdict(set)
    for vault, asset_address in zip(all_vault_addresses, asset_addresses):
        vaults_by_token[asset_address].add(vault)

    return vaults_by_token


async def get_silo_vaults(config_address: str):
    w3 = await get_w3(IntChainId.Sonic)
    silo_vaults = await (
        w3.eth.contract(address=config_address, abi=ABI.SILO_CONFIG)
        .functions.getSilos()
        .call()
    )

    return silo_vaults


async def get_asset_address_from_vault(vault_address: str):
    w3 = await get_w3(IntChainId.Sonic)
    return (
        await w3.eth.contract(address=vault_address, abi=ABI.SILO)
        .functions.asset()
        .call()
    )


async def get_user_balance_in_vault(vault_address: str, user_address: str):
    w3 = await get_w3(IntChainId.Sonic)
    contract = w3.eth.contract(address=vault_address, abi=ABI.SILO)
    return await contract.functions.balanceOf(user_address).call()
