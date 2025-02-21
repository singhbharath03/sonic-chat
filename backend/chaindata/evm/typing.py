from typing import List, Optional

from pydantic import BaseModel


class TokenMetadata_(BaseModel):
    name: str
    symbol: str
    decimals: Optional[int] = None
    logo_url: Optional[str] = None
    total_supply: Optional[float] = None


class TokenHolding(BaseModel):
    token_address: str
    balance: float
    name: str
    symbol: str
    decimals: int
    logo_url: Optional[str] = None
    price: Optional[float] = None
    usd_value: Optional[float] = None


class TokenHoldings(BaseModel):
    holdings: List[TokenHolding]
    total_usd_value: float
