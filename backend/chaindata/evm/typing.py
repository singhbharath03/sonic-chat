from typing import Optional

from pydantic import BaseModel


class TokenMetadata_(BaseModel):
    name: str
    symbol: str
    decimals: Optional[int] = None
    logo_url: Optional[str] = None
    total_supply: Optional[float] = None
