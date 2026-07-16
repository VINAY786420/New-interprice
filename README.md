# Interprice - Social Media Data Collection Centre

A comprehensive platform for collecting and analyzing social media data.

## Project Structure

```
interprice/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration for backend
├── render.yaml           # Render.com deployment configuration
├── .gitignore            # Git ignore rules
├── backend/              # Backend service (to be created)
├── frontend/             # Frontend service (to be created)
├── scrapers/             # Data scraping service (to be created)
└── admin/                # Admin panel service (to be created)
```

## Requirements

- Python 3.11+
- Flask
- Requests
- BeautifulSoup4
- Selenium
- Pandas

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

The application will start on port 8000.

## Docker

Build and run with Docker:
```bash
docker build -t interprice .
docker run -p 8000:8000 interprice
```

## Deployment

The project is configured for deployment on [Render.com](https://render.com) using `render.yaml`.

## API Endpoints

- `GET /` - Health check and app info
- `GET /health` - Health status
- `GET /api/v1/data` - Social media data collection endpoint

## Status

✅ Backend: Configured
⏳ Frontend: Pending
⏳ Scrapers: Pending
⏳ Admin Panel: Pending
