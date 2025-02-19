import json

from chaindata.constants import SONIC_CHAIN_ID, IntChainId
from tools.http import req_post

quote_url = "https://api.odos.xyz/sor/quote/v2"


async def get_quote(
    chain_id: IntChainId,
    input_token_address: str,
    input_token_amount: int,
    output_token_address: str,
    user_addr: str,
    referral_code: int = 0,
    slippage_limit_percent: float = 1,
    disable_rfqs: bool = True,
    compact: bool = True,
):
    # only supports sonic chain for now
    chain_id = SONIC_CHAIN_ID
    quote_request_body = {
        "chainId": chain_id,  # Replace with desired chainId
        "inputTokens": [
            {
                "tokenAddress": input_token_address,
                "amount": str(input_token_amount),
            }
        ],
        "outputTokens": [
            {
                "tokenAddress": output_token_address,
                "proportion": 1,
            }
        ],
        "slippageLimitPercent": slippage_limit_percent,
        "userAddr": user_addr,
        "referralCode": referral_code,
        "disableRFQs": disable_rfqs,
        "compact": compact,
    }

    return await req_post(quote_url, quote_request_body)
