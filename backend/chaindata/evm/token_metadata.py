import logging
from typing import Dict, List

from chaindata.evm.token_lists import get_token_lists
from chaindata.evm.typing import TokenMetadata_

logger = logging.getLogger(__name__)


async def get_token_metadata(token_addresses: List[str]) -> Dict[str, TokenMetadata_]:
    metadata_by_mint = {}
    token_list = await get_token_lists()
    for token in token_list:
        if token["address"] in token_addresses:
            metadata_by_mint[token["address"]] = TokenMetadata_(
                name=token.get("name"),
                symbol=token.get("symbol"),
                decimals=token.get("decimals"),
                logo_url=f"https://raw.githubusercontent.com/Shadow-Exchange/shadow-assets/main/blockchains/sonic/assets/{token['address']}/logo.png",
            )

    if "0x0000000000000000000000000000000000000000" in token_addresses:
        metadata_by_mint["0x0000000000000000000000000000000000000000"] = (
            get_sonic_token_metadata()
        )

    return metadata_by_mint


def get_sonic_token_metadata():
    return TokenMetadata_(
        name="Sonic",
        symbol="SONIC",
        decimals=18,
        logo_url="https://sonicscan.org/token/images/s-token.svg",
    )
