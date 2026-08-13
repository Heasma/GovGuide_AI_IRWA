"""
GovGuide AI — User ORM Model

STABLE TABLE: This schema is unlikely to change significantly.
"""

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.orm import relationship

from app.models.base import Base, uuid_pk, now


class User(Base):
    """Application user — supports PUBLIC, CITIZEN, ADMIN roles."""
    __tablename__ = "users"

    id = uuid_pk()
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt — never plaintext
    role = Column(
        Enum("public", "citizen", "admin", name="user_role_enum"),
        nullable=False,
        default="public",
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = now()
    last_login = Column(DateTime(timezone=True), nullable=True)

    sessions = relationship("QuerySession", back_populates="user", lazy="select")


__all__ = ["User"]
