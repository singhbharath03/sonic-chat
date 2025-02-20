from functools import reduce
from typing import List


def get_from_dict(dataDict, mapList, default=None):
    """Iterate nested dictionary"""
    try:
        return reduce(lambda d, k: d[k], mapList, dataDict)
    except (KeyError, TypeError):
        return default
