import os
import asyncio
import base64
from typing import Any, Dict

from tools.typing import UserDetails
from tools.http import req_get

PRIVY_APP_ID = os.getenv("PRIVY_APP_ID")
PRIVY_APP_SECRET = os.getenv("PRIVY_APP_SECRET")


async def get_user_profile(user_privy_id: str) -> UserDetails:
    user_details = await get_user_details(user_privy_id)
    evm_wallet_address, solana_wallet_address = _get_wallet_addresses(user_details)

    return UserDetails(
        id=user_privy_id,
        evm_wallet_address=evm_wallet_address,
        solana_wallet_address=solana_wallet_address,
    )


def _get_wallet_addresses(user_details: dict):
    evm_wallet_address = None
    solana_wallet_address = None
    for linked_account_details in user_details["linked_accounts"]:
        if (
            linked_account_details["type"] == "wallet"
            and linked_account_details["connector_type"] == "embedded"
        ):
            if linked_account_details["chain_type"] == "solana":
                solana_wallet_address = linked_account_details["address"]
            else:
                evm_wallet_address = linked_account_details["address"]

    return evm_wallet_address, solana_wallet_address


async def get_user_details(user_privy_id: str):
    url = f"https://auth.privy.io/api/v1/users/{_get_did_from_user_id(user_privy_id)}"

    auth_string = base64.b64encode(
        f"{PRIVY_APP_ID}:{PRIVY_APP_SECRET}".encode()
    ).decode()
    headers = {
        "Authorization": f"Basic {auth_string}",
        "privy-app-id": PRIVY_APP_ID,
    }

    return await req_get(url, headers=headers)


def _get_did_from_user_id(user_id: str) -> str:
    # user_id format -> did:privy:XXXXXX.

    return user_id.split("did:privy:")[1]
