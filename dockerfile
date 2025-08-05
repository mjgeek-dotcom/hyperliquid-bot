# Multi-stage build for production
FROM python:3.12-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY . .

# Security hardening
RUN useradd -m trader && \
    chown -R trader:trader /app && \
    chmod 755 /app/scripts/*.sh

USER trader
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

CMD ["python", "-m", "bot.main"]