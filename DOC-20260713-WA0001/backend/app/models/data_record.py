"""Individual data record model."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, BigInteger, Float, Text
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class DataRecord(Base, TimestampMixin):
    """Individual collected data record."""
    __tablename__ = "data_records"

    id = Column(Integer, primary_key=True, index=True)

    # Source
    platform = Column(String(50), nullable=False, index=True)  # twitter, instagram
    source_id = Column(String(255), index=True)  # Original platform ID
    source_url = Column(Text)

    # Content
    username = Column(String(255), index=True)
    display_name = Column(String(255))
    profile_url = Column(Text)
    bio = Column(Text)

    # Engagement
    followers_count = Column(BigInteger, default=0)
    following_count = Column(BigInteger, default=0)
    posts_count = Column(BigInteger, default=0)
    engagement_rate = Column(Float)

    # Content data
    post_content = Column(Text)
    post_type = Column(String(50))  # text, image, video, reel
    hashtags = Column(JSON)
    mentions = Column(JSON)

    # Media
    media_urls = Column(JSON)
    thumbnail_url = Column(Text)

    # Metrics
    likes_count = Column(BigInteger, default=0)
    comments_count = Column(BigInteger, default=0)
    shares_count = Column(BigInteger, default=0)
    views_count = Column(BigInteger, default=0)

    # Enrichment
    sentiment_score = Column(Float)  # -1 to 1
    sentiment_label = Column(String(20))  # positive, negative, neutral
    language = Column(String(10))
    topics = Column(JSON)

    # Location
    country = Column(String(100), index=True)
    city = Column(String(100))
    coordinates = Column(JSON)  # {"lat": x, "lng": y}

    # Demographics (inferred)
    estimated_age_range = Column(String(20))
    estimated_gender = Column(String(20))
    interests = Column(JSON)

    # Metadata
    posted_at = Column(DateTime, index=True)
    collected_at = Column(DateTime)
    is_verified = Column(Boolean, default=False)
    is_business_account = Column(Boolean, default=False)

    # Compliance
    pii_redacted = Column(Boolean, default=False)
    consent_status = Column(String(50), default="public")  # public, opt-in, opt-out

    # Raw data backup
    raw_data = Column(JSON)

    # Relationships
    collection_id = Column(Integer, ForeignKey("collections.id"))
    collection = relationship("Collection", back_populates="records")

    # Indexes for performance
    __table_args__ = (
        {"postgresql_using": "gin"},
    )
