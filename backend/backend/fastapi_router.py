from fastapi import FastAPI
from chat.views import router as chat_router


def setup_routers(app: FastAPI):
    """Routes"""
    app.include_router(chat_router, prefix="/chat")
