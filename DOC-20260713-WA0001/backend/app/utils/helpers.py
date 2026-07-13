"""Utility helper functions."""
import re
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)

    # Remove special characters but keep emojis
    text = re.sub(r'[^\w\s\U0001F300-\U0001F9FF]', '', text)

    return text.strip()


def extract_hashtags(text: str) -> list:
    """Extract hashtags from text."""
    if not text:
        return []
    return re.findall(r'#(\w+)', text)


def extract_mentions(text: str) -> list:
    """Extract mentions from text."""
    if not text:
        return []
    return re.findall(r'@(\w+)', text)


def calculate_engagement_rate(likes: int, comments: int, shares: int, followers: int) -> float:
    """Calculate engagement rate percentage."""
    if followers == 0:
        return 0.0

    total_engagement = likes + comments + shares
    rate = (total_engagement / followers) * 100
    return round(rate, 2)


def generate_hash(data: Dict[str, Any]) -> str:
    """Generate a hash for deduplication."""
    content = str(sorted(data.items()))
    return hashlib.md5(content.encode()).hexdigest()


def parse_date(date_string: str, formats: list = None) -> Optional[datetime]:
    """Parse date string with multiple formats."""
    if not date_string:
        return None

    if formats is None:
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    return None


def format_number(num: int) -> str:
    """Format large numbers (1K, 1M, 1B)."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def redact_pii(text: str) -> str:
    """Redact personally identifiable information."""
    if not text:
        return text

    # Redact email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)

    # Redact phone numbers (Indian format)
    text = re.sub(r'\b\d{10}\b', '[PHONE_REDACTED]', text)
    text = re.sub(r'\+91[-\s]?\d{10}', '[PHONE_REDACTED]', text)

    # Redact Aadhaar numbers
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[AADHAAR_REDACTED]', text)

    return text


def estimate_demographics(bio: str, posts: list) -> Dict[str, Any]:
    """Estimate demographics from profile data (basic heuristic)."""
    demographics = {
        "estimated_age_range": None,
        "estimated_gender": None,
        "interests": []
    }

    # Simple keyword-based estimation
    text = (bio or "").lower()

    # Age indicators
    age_keywords = {
        "teen": "13-19",
        "student": "18-24",
        "college": "18-24",
        "young": "20-30",
        "professional": "25-40",
        "parent": "30-50",
        "retired": "60+",
    }

    for keyword, age_range in age_keywords.items():
        if keyword in text:
            demographics["estimated_age_range"] = age_range
            break

    # Interest extraction
    interest_keywords = [
        "technology", "business", "fashion", "food", "travel",
        "sports", "music", "photography", "art", "fitness",
        "gaming", "politics", "education", "health", "finance"
    ]

    demographics["interests"] = [
        interest for interest in interest_keywords
        if interest in text
    ]

    return demographics
