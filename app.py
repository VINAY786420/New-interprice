# Root app.py moved to backend/app.py to avoid deployment confusion.
# If you need this file for local testing, run backend/app.py directly or use the backend Dockerfile.

# The real backend application now lives at backend/app.py and is served by gunicorn in production.
print('This repository uses backend/app.py as the backend application. See backend/ for the real source.')
