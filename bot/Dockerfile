FROM python:3.11-slim

WORKDIR /app

# Install git and Google Cloud SDK
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ca-certificates \
    && curl -sSL https://sdk.cloud.google.com | bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/google-cloud-sdk/bin:${PATH}"

COPY bot/requirements.txt /app/bot/requirements.txt
RUN pip install --no-cache-dir -r /app/bot/requirements.txt

COPY . /app/

CMD ["python", "-m", "bot.main"]
