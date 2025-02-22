from chaindata.evm.token_metadata import get_sonic_token_metadata
from chat.txn_builder import build_transaction_request
from chat.typing import SonicStakeTxnSteps, TransactionFlows
from chaindata.constants import IntChainId
from chaindata.evm.utils import get_w3
from chaindata.evm.constants import ABI
from chat.models import Conversation, TransactionRequests

SONIC_FORWARD_PROXY_CONTRACT = "0xFC00FACE00000000000000000000000000000000"
TOP_SELF_STAKE_VALIDATOR_ID = 18

"""
TODO: Fetch top stakers from below curl instead of hardcoding

curl 'https://xapi.sonic.soniclabs.com/' \
  -H 'accept: application/graphql-response+json' \
  -H 'accept-language: en-US,en-IN;q=0.9,en;q=0.8' \
  -H 'content-type: application/json' \
  -H 'origin: https://my.soniclabs.com' \
  -H 'priority: u=1, i' \
  -H 'referer: https://my.soniclabs.com/' \
  -H 'sec-ch-ua: "Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-site' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36' \
  --data-raw '{"query":"\n    query Validators {\n  stakers {\n    id\n    isActive\n    stake\n    stakerAddress\n    stakerInfo {\n      logoUrl\n      name\n    }\n    delegatedLimit\n    totalStake\n    totalDelegatedLimit\n  }\n}\n    ","variables":{}}'
"""


async def stake_sonic(
    conversation: Conversation,
    user_address: str,
    amount: float,
) -> bool:
    transaction_request = await build_transaction_request(
        conversation,
        user_address,
        TransactionFlows.STAKE_SONIC,
        {"amount": amount},
    )
    await transaction_request.asave()

    return await process_stake_sonic_transaction(transaction_request)


async def process_stake_sonic_transaction(
    transaction_request: TransactionRequests,
) -> bool:
    user_address = transaction_request.user_address
    amount = transaction_request.data["amount"]

    if transaction_request.step < SonicStakeTxnSteps.STAKE:
        w3 = await get_w3(IntChainId.Sonic)
        contract = w3.eth.contract(address=SONIC_FORWARD_PROXY_CONTRACT, abi=ABI.SFC)

        txn = await contract.functions.delegate(
            TOP_SELF_STAKE_VALIDATOR_ID
        ).build_transaction(
            {
                "from": user_address,
                "value": amount,
            }
        )

        transaction_request.transaction_details = {
            "transaction": txn,
            "description": f"Staking {amount} SONIC",
        }
        await transaction_request.asave()

        return True

    return False
