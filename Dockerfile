FROM python:3.12.8-slim

WORKDIR /app
COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 4173
CMD ["python3", "server.py", "--host", "0.0.0.0", "--port", "4173"]
