FROM python:3.11-slim

WORKDIR /app/backend

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

ENV PORT=8000
EXPOSE 8000

# Use gunicorn for production
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "2"]
