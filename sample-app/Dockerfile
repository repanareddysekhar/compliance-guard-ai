# VIOLATION: Using 'latest' tag
FROM python:3.9-slim-buster

# VIOLATION: Running as root user (no USER instruction)
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# VIOLATION: Missing HEALTHCHECK instruction
CMD ["python", "src/auth.py"]
