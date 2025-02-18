FROM ubuntu:24.04

ENV PYTHONUNBUFFERED=TRUE
ENV DEBIAN_FRONTEND="noninteractive"
ENV LC_ALL=en_US.utf-8
ENV LANG=en_US.utf-8

RUN apt-get update && \
    apt-get install -y build-essential sudo && \
    apt-get install -y postgresql-client curl libpq-dev && \
    apt-get install -y software-properties-common wget curl
# apt-get install -y --fix-missing python3-pip && \
# apt-get install -y python3-dev python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info && \
# apt-get install wget

RUN add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.12 python3.12-dev python3.12-venv

RUN mkdir /config
ADD config/requirements.txt /config/requirements.txt
ADD config/requirements-dev.txt /config/requirements-dev.txt

RUN python3.12 -m venv /venv
ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --no-cache -r /config/requirements.txt
RUN pip install --no-cache -r /config/requirements-dev.txt

# Add app source.
# Dev envs are expected to volume mount the source to /app for hot reloads.
ADD backend /app
WORKDIR /app

# CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--reload", "backend.asgi:app", "--timeout", "120", "--graceful-timeout", "0"]
CMD ["uvicorn", "backend.asgi:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]