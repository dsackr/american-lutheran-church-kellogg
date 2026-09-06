FROM python:3.11-slim

WORKDIR /app

# Copy website and server files
COPY . /app/

ENV PORT=8080
EXPOSE 8080

CMD ["python3", "api/main.py"]

