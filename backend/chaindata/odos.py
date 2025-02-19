from chaindata.constants import SONIC_CHAIN_ID, IntChainId
from tools.http import req_post

BASE_URL = "https://api.odos.xyz/sor"


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

    return await req_post(f"{BASE_URL}/quote/v2", quote_request_body)


async def assemble_transaction(quote_response: dict, user_addr: str):
    assemble_request_body = {
        "userAddr": user_addr,
        "pathId": quote_response[
            "pathId"
        ],  # Replace with the pathId from quote response in step 1
        "simulate": False,  # this can be set to true if the user isn't doing their own estimate gas call for the transaction
    }

    return await req_post(f"{BASE_URL}/assemble", assemble_request_body)
