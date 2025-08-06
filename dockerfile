FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt && \
    useradd -m trader && \
    chown -R trader:trader /app

USER trader

CMD ["python", "-m", "bot.main"]
