from pydantic import BaseModel


class UserDetails(BaseModel):
    id: str
    evm_wallet_address: str
    solana_wallet_address: str
