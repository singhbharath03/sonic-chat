import logging
from typing import List, Optional

from chat.typing import ChatResponse_, Message_, ProcessMessageRequest_
from chat.llm_conversation import NEW_THREAD_START_MESSAGES, process_chat
from fastapi import APIRouter, Request, FastAPI, HTTPException


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/test/")
async def test(request: Request):
    return {"message": "Hello, World!"}


@router.post("/process_messages/")
async def process_message(request: ProcessMessageRequest_) -> ProcessMessageRequest_:
    messages = await process_chat(request.messages)
    return ProcessMessageRequest_(messages=messages)


@router.get("/new_thread/", response_model=ChatResponse_)
async def new_thread(request: Request) -> ChatResponse_:
    messages = [
        Message_(
            role="system",
            content="You are a helpful AI assistant whose goal is to help onboard users to Sonic chain...",
        ),
        Message_(
            role="assistant",
            content="Hello! I'm here to help you get started on Sonic Chain.",
        ),
    ]
    return ChatResponse_(messages=messages)
