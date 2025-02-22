from typing import List
import asyncio

from chaindata.constants import ACTIVE_CHAINS, IntChainId
from chaindata.evm.utils import get_w3
from tenacity import retry, stop_after_attempt, wait_exponential


async def get_active_chains(wallet_address: str) -> List[str]:
    """Returns the list of active chains for a given wallet address."""

    tasks = [get_native_balance(chain_id, wallet_address) for chain_id in ACTIVE_CHAINS]
    balances = await asyncio.gather(*tasks)

    return [
        IntChainId.get_str(chain_id)
        for chain_id, balance in zip(ACTIVE_CHAINS, balances)
        if balance > 0
    ]


@retry(
    stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.1, min=0.2, max=1.0)
)
async def get_native_balance(chain_id: IntChainId, wallet_address: str) -> int:
    w3 = await get_w3(chain_id)
    balance = await w3.eth.get_balance(wallet_address)
    return balance
