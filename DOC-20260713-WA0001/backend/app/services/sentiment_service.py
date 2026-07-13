"""Sentiment analysis service for data enrichment."""
from typing import Optional, Dict
import re

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False


class SentimentAnalyzer:
    """Analyze sentiment of social media content."""

    # Hindi sentiment keywords
    POSITIVE_HINDI = [
        "अच्छा", "बढ़िया", "शानदार", "जबरदस्त", "प्यार", "खूबसूरत",
        "सुंदर", "मजेदार", "शानदार", "उम्दा", "जानदार", "दमदार"
    ]

    NEGATIVE_HINDI = [
        "बुरा", "घटिया", "बेकार", "नफरत", "गंदा", "खराब",
        "धोखा", "झूठ", "बकवास", "फालतू", "घटिया", "बेहूदा"
    ]

    def __init__(self):
        self.use_textblob = TEXTBLOB_AVAILABLE

    def analyze(self, text: str, language: str = "en") -> Dict:
        """Analyze sentiment of text."""
        if not text:
            return {"score": 0.0, "label": "neutral", "confidence": 0.0}

        if language == "hi" or self._is_hindi(text):
            return self._analyze_hindi(text)

        return self._analyze_english(text)

    def _analyze_english(self, text: str) -> Dict:
        """Analyze English text sentiment."""
        if self.use_textblob:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
        else:
            polarity = self._simple_sentiment_score(text)
            subjectivity = 0.5

        # Determine label
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"

        confidence = abs(polarity) + (subjectivity * 0.3)
        confidence = min(confidence, 1.0)

        return {
            "score": round(polarity, 3),
            "label": label,
            "confidence": round(confidence, 3),
            "subjectivity": round(subjectivity, 3)
        }

    def _analyze_hindi(self, text: str) -> Dict:
        """Analyze Hindi text sentiment using keyword matching."""
        positive_count = sum(1 for word in self.POSITIVE_HINDI if word in text)
        negative_count = sum(1 for word in self.NEGATIVE_HINDI if word in text)

        total = positive_count + negative_count
        if total == 0:
            return {"score": 0.0, "label": "neutral", "confidence": 0.0}

        score = (positive_count - negative_count) / total

        if score > 0.1:
            label = "positive"
        elif score < -0.1:
            label = "negative"
        else:
            label = "neutral"

        confidence = abs(score) * (total / max(len(text.split()), 1))
        confidence = min(confidence, 1.0)

        return {
            "score": round(score, 3),
            "label": label,
            "confidence": round(confidence, 3)
        }

    def _is_hindi(self, text: str) -> bool:
        """Check if text contains Hindi characters."""
        hindi_range = range(0x0900, 0x097F)
        return any(ord(char) in hindi_range for char in text)

    def _simple_sentiment_score(self, text: str) -> float:
        """Simple keyword-based sentiment scoring."""
        positive_words = [
            "good", "great", "excellent", "amazing", "love", "best",
            "awesome", "fantastic", "wonderful", "perfect", "happy",
            "beautiful", "nice", "cool", "super", "brilliant"
        ]
        negative_words = [
            "bad", "terrible", "awful", "hate", "worst", "horrible",
            "disgusting", "pathetic", "useless", "stupid", "sad",
            "angry", "disappointed", "boring", "annoying"
        ]

        words = re.findall(r'\b\w+\b', text.lower())

        positive = sum(1 for w in words if w in positive_words)
        negative = sum(1 for w in words if w in negative_words)
        total = positive + negative

        if total == 0:
            return 0.0

        return (positive - negative) / total


# Singleton instance
sentiment_analyzer = SentimentAnalyzer()
