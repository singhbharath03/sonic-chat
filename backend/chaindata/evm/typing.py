from typing import List, Optional

from tools.typing import DisplayValue_
from pydantic import BaseModel


class TokenMetadata_(BaseModel):
    name: str
    symbol: str
    decimals: Optional[int] = None
    logo_url: Optional[str] = None
    total_supply: Optional[float] = None


class TokenHolding(BaseModel):
    token_address: str
    balance: Optional[DisplayValue_] = None
    name: str
    symbol: str
    decimals: int
    logo_url: Optional[str] = None
    price: Optional[DisplayValue_] = None
    usd_value: Optional[DisplayValue_] = None


class TokenHoldings(BaseModel):
    holdings: List[TokenHolding]
    total_usd_value: Optional[DisplayValue_] = None
