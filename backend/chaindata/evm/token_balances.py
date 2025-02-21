from typing import Dict, List, Optional
import asyncio

from pydantic import BaseModel

from chaindata.evm.pricing import get_latest_prices
from chaindata.evm.typing import TokenHolding, TokenHoldings
from chaindata.evm.token_metadata import get_token_metadata
from chaindata.evm.token_lists import get_token_lists
from chaindata.evm.utils import SONIC_RPC_URL
from tools.http import req_post


async def get_sonic_token_holdings(user_address: str) -> TokenHoldings:
    token_list = await get_token_lists()
    token_addresses = [token["address"] for token in token_list]
    token_addresses_with_native = token_addresses + [
        "0x0000000000000000000000000000000000000000"
    ]

    balances, metadata_by_mint, prices = await asyncio.gather(
        get_user_token_balances(user_address, token_addresses),
        get_token_metadata(token_addresses_with_native),
        get_latest_prices(token_addresses_with_native),
    )

    token_holdings = []
    total_usd_value = 0
    for token_address, balance in balances.items():
        if balance <= 0:
            continue

        decimal_adjusted_balance = balance / (
            10 ** metadata_by_mint[token_address].decimals
        )

        token_price = prices.get(token_address)
        usd_value = None
        if token_price is not None:
            usd_value = token_price * decimal_adjusted_balance
            total_usd_value += usd_value

        token_holdings.append(
            TokenHolding(
                token_address=token_address,
                balance=decimal_adjusted_balance,
                name=metadata_by_mint[token_address].name,
                symbol=metadata_by_mint[token_address].symbol,
                decimals=metadata_by_mint[token_address].decimals,
                logo_url=metadata_by_mint[token_address].logo_url,
                price=token_price,
                usd_value=usd_value,
            )
        )

    return TokenHoldings(
        holdings=token_holdings,
        total_usd_value=total_usd_value,
    )


async def get_all_token_balances(user_address: str) -> Dict[str, str]:
    token_list = await get_token_lists()
    token_addresses = [token["address"] for token in token_list]
    return await get_user_token_balances(user_address, token_addresses)


async def get_user_token_balances(
    user_address: str, token_addresses: List[str]
) -> Dict[str, str]:
    requests = [
        get_user_token_balance_req(user_address, token_address)
        for token_address in token_addresses
    ] + [get_native_balance_req(user_address)]

    responses = await req_post(SONIC_RPC_URL, requests)

    balances = {}
    # Handle token balances (all except the last response which is native balance)
    for token_address, resp in zip(token_addresses, responses[:-1]):
        resp_json = resp["result"]
        if resp_json is None:
            raise ValueError(f"No balance found for token {token_address}")

        balance = int(resp_json, 16)
        balances[token_address] = balance

    # Handle native balance (last response)
    native_resp = responses[-1]
    if native_resp["result"] is not None:
        balances["0x0000000000000000000000000000000000000000"] = int(
            native_resp["result"], 16
        )

    return balances


def get_user_token_balance_req(
    user_address: str, token_address: str, block_id: str = "latest"
) -> dict:
    data = "0x70a08231000000000000000000000000" + user_address[2:]  # [2:] to strip "0x"
    # For understanding this, see: https://stackoverflow.com/questions/48228662/get-token-balance-with-ethereum-rpc
    return {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [
            {"to": token_address, "data": data},
            block_id,
        ],
        "id": f"r:{user_address}_{token_address}_{block_id}",
    }


def get_native_balance_req(user_address: str, block_id: str = "latest"):
    return {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [user_address, block_id],
        "id": f"{user_address}_{block_id}_get_eth_bal",
    }
