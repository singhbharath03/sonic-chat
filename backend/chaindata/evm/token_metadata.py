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
            )

    return metadata_by_mint
