from pydantic import BaseModel
from typing import Optional


class UserDetails(BaseModel):
    id: str
    evm_wallet_address: str
    solana_wallet_address: str


class DisplayValue_(BaseModel):
    value: float
    display_value: Optional[str]
