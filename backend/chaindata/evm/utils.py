import os

from web3 import Web3, AsyncWeb3

from chaindata.constants import ACTIVE_CHAINS, IntChainId

BASE_RPC_URL = os.getenv("BASE_RPC_URL")
SONIC_RPC_URL = os.getenv("SONIC_RPC_URL")


async def get_w3(chain_id: IntChainId):
    if chain_id == IntChainId.Sonic:
        w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(SONIC_RPC_URL))
    elif chain_id == IntChainId.Base:
        w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(BASE_RPC_URL))
    elif chain_id in ACTIVE_CHAINS:
        raise NotImplementedError(f"Chain {chain_id} not supported yet")
    else:
        raise ValueError(f"Unsupported chain id: {chain_id}")

    return w3
