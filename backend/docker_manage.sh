#!/bin/bash
exec docker exec -it sonic-chat-django-1 python3 manage.py "$@"
