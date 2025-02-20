from typing import Dict, List, Optional
import asyncio

from pydantic import BaseModel

from chaindata.evm.typing import TokenHolding
from chaindata.evm.token_metadata import get_token_metadata
from chaindata.evm.token_lists import get_token_lists
from chaindata.evm.utils import SONIC_RPC_URL
from tools.http import req_post


async def get_sonic_token_holdings(user_address: str) -> List[TokenHolding]:
    token_list = await get_token_lists()
    token_addresses = [token["address"] for token in token_list]

    balances, metadata_by_mint = await asyncio.gather(
        get_user_token_balances(user_address, token_addresses),
        get_token_metadata(token_addresses),
    )

    return [
        TokenHolding(
            token_address=token_address,
            balance=balance / (10 ** metadata_by_mint[token_address].decimals),
            name=metadata_by_mint[token_address].name,
            symbol=metadata_by_mint[token_address].symbol,
            decimals=metadata_by_mint[token_address].decimals,
            logo_url=metadata_by_mint[token_address].logo_url,
        )
        for token_address, balance in balances.items()
        if balance > 0
    ]


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
    ]

    resp = await req_post(SONIC_RPC_URL, requests)

    balances = {}
    for token_address, resp in zip(token_addresses, resp):
        resp_json = resp["result"]
        if resp_json is None:
            raise ValueError(f"No balance found for token {token_address}")

        balance = int(resp_json, 16)
        balances[token_address] = balance

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
