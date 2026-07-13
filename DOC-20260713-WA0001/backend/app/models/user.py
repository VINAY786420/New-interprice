"""User model for authentication and authorization."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.models.base import Base, TimestampMixin


class UserRole(PyEnum):
    """User roles for RBAC."""
    ADMIN = "admin"
    OPERATOR = "operator"
    BUYER = "buyer"
    VIEWER = "viewer"


class User(Base, TimestampMixin):
    """User account model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.OPERATOR)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime)

    # Relationships
    collections = relationship("Collection", back_populates="owner")
    buyer_profile = relationship("Buyer", back_populates="user", uselist=False)
