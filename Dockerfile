FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs tests

EXPOSE 8000

FROM base AS production
CMD ["python", "main.py", "health"]

FROM base AS dev
CMD ["python", "main.py", "chat"]

FROM base AS api
EXPOSE 8000
CMD ["python", "main.py", "serve"]
