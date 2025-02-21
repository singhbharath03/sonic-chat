from tools.http import req_get


async def get_latest_prices(token_addresses: list[str]):
    resp = await get_whitelisted_token_prices_from_odos()

    return {
        token_address: resp["tokenPrices"].get(token_address)
        for token_address in token_addresses
    }


async def get_whitelisted_token_prices_from_odos():
    return await req_get("https://api.odos.xyz/pricing/token/146?currencyId=USD")
