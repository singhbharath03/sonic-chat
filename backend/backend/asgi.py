"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

django_app = get_asgi_application()

from importlib.util import find_spec
from typing import Union

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from django.conf import settings

from .fastapi_router import setup_routers

app = FastAPI(swagger_ui_parameters={"displayRequestDuration": True}, root_path="/api")
app.mount("/admin", django_app)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


setup_routers(app)
