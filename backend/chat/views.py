import logging
from typing import List

from fastapi import APIRouter, Request, FastAPI, HTTPException


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/test/")
async def test(request: Request):
    return {"message": "Hello, World!"}
