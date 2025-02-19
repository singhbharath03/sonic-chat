from typing import Type, T
from functools import lru_cache

from django.db import models

SONIC_CHAIN_ID = 146


class BaseIntEnum(models.IntegerChoices):
    @classmethod
    def get_instance(cls: Type[T], enum, values=None) -> T:  # Added 'values' parameter
        if isinstance(enum, str):
            try:
                value = getattr(cls, enum)
                if isinstance(value, cls):
                    return value
                else:
                    raise ValueError(f"'{enum}' is not a valid enum member")
            except AttributeError as e:
                # Pydantic catches ValueError and throws ValidationError
                raise ValueError(str(e))
        elif isinstance(enum, int):
            return cls(enum)
        elif isinstance(enum, cls):
            return enum

        raise ValueError(f"Invalid enum type {enum}")

    @classmethod
    def __get_validators__(cls):
        yield cls.get_instance


class IntChainId(BaseIntEnum):
    _Any = 0  # Unique identifier for dumped data which is true across chains
    Sonic = 1
    Base = 2

    @classmethod
    @lru_cache
    def for_chain(cls, chain_id):
        return cls.get_instance(chain_id)

    @classmethod
    def get_str(cls, chain_id) -> str:
        return cls.for_chain(chain_id)._name_

    @classmethod
    def get_int(cls, chain_id) -> int:
        return cls.for_chain(chain_id)._value_

    @classmethod
    def all_chains(cls):
        return set(cls) - set([cls._Any])

    @classmethod
    def all_str_chain_ids(cls):
        return {cls.get_str(chain_id) for chain_id in cls.all_chains()}


ACTIVE_CHAINS = [IntChainId.Sonic, IntChainId.Base]
