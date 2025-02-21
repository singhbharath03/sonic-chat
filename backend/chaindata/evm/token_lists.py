import logging
from typing import Dict, List

from chaindata.constants import SONIC_NATIVE_TOKEN_PLACEHOLDER_ADDRESS
from tools.http import req_get

logger = logging.getLogger(__name__)

_TOKEN_LISTS_CACHE = None


async def get_token_addresses_from_symbols(symbols: List[str]) -> Dict[str, str]:
    # TODO: Handle symbols by chain

    token_list = await get_token_lists()

    # Hardcode native token for sonic chain
    token_list.append(
        {
            "name": "Sonic",
            "symbol": "S",
            "address": SONIC_NATIVE_TOKEN_PLACEHOLDER_ADDRESS,
            "decimals": 18,
        }
    )

    return {token["symbol"]: token["address"] for token in token_list}


async def get_token_lists():
    global _TOKEN_LISTS_CACHE

    SHADOW_EXCHANGE_TOKEN_LIST_URL = "https://raw.githubusercontent.com/Shadow-Exchange/shadow-assets/main/blockchains/sonic/tokenlist.json"

    if _TOKEN_LISTS_CACHE is None:
        try:
            data = await req_get(SHADOW_EXCHANGE_TOKEN_LIST_URL, timeout=5)
        except TimeoutError:
            logger.warning("Fetching token list from Solana Cloud timed out")
            data = {}

        _TOKEN_LISTS_CACHE = data.get("tokens", [[]])[0]

    return _TOKEN_LISTS_CACHE
