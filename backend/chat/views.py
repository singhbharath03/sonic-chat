import logging
from typing import List, Optional

from chat.models import Conversation
from tools.privy import get_user_profile
from chat.typing import (
    ChatResponse_,
    ConversationResponse_,
    Message_,
    ProcessMessageRequest_,
)
from chat.llm_conversation import NEW_THREAD_START_MESSAGES, complete_conversation
from fastapi import APIRouter, Request, FastAPI, HTTPException


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/test/")
async def test(request: Request):
    return {"message": "Hello, World!"}


@router.post("/process_messages/")
async def process_message(
    request: ProcessMessageRequest_, privy_user_id: str
) -> ConversationResponse_:
    # Get conversation, add new message and save
    conversation = await Conversation.objects.aget(id=request.id)
    conversation.messages.append({"role": "user", "content": request.user_message})
    await conversation.asave()

    user_details = await get_user_profile(privy_user_id)
    await complete_conversation(conversation, user_details)

    return ConversationResponse_(id=conversation.id, messages=conversation.messages)


@router.get("/new_thread/", response_model=ConversationResponse_)
async def new_thread(request: Request, privy_user_id: str) -> ConversationResponse_:
    conversation = await Conversation.objects.acreate(
        user_id=privy_user_id, messages=NEW_THREAD_START_MESSAGES
    )

    return ConversationResponse_(id=conversation.id, messages=conversation.messages)
