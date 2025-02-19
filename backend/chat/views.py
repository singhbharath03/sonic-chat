import logging
from typing import List, Optional

from tools.privy import get_user_profile
from chat.typing import ChatResponse_, Message_, ProcessMessageRequest_
from chat.llm_conversation import NEW_THREAD_START_MESSAGES, process_chat
from fastapi import APIRouter, Request, FastAPI, HTTPException


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/test/")
async def test(request: Request):
    return {"message": "Hello, World!"}


@router.post("/process_messages/")
async def process_message(
    request: ProcessMessageRequest_, privy_user_id: str
) -> ProcessMessageRequest_:
    user_details = await get_user_profile(privy_user_id)
    messages = await process_chat(request.messages, user_details)
    return ProcessMessageRequest_(messages=messages)


@router.get("/new_thread/", response_model=ChatResponse_)
async def new_thread(request: Request, privy_user_id: str) -> ChatResponse_:
    return ChatResponse_(messages=NEW_THREAD_START_MESSAGES)
