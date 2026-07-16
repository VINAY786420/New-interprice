FROM python:3.11-slim

WORKDIR /app

# Install dependencies (requirements.txt is expected in the build context root)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source (build context for this Dockerfile is the backend/ directory)
COPY . .

ENV PORT=8000
EXPOSE 8000

# Use gunicorn for production
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "2"]
