FROM python:3.11-slim

WORKDIR /app

# Install dependencies (requirements.txt is expected in the build context root)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source files (build context is backend/ when Render uses backend/Dockerfile)
COPY . .

ENV PORT=8000
EXPOSE 8000

# Add a healthcheck using Python (curl may not be available in slim)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import sys,urllib.request as u; r=u.urlopen('http://127.0.0.1:8000/health'); sys.exit(0 if r.getcode()==200 else 1)"

# Use gunicorn for production
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "2"]
