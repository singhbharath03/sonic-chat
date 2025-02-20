import logging

from tools.http import req_get

logger = logging.getLogger(__name__)

_TOKEN_LISTS_CACHE = None


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
