"""
User model for authentication and user management.
"""
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class User(BaseModel):
    """
    User model for authentication and user management.

    Attributes:
        id: Unique user identifier (UUID)
        email: User email address (unique)
        phone: User phone number
        password_hash: Hashed password
        first_name: User first name
        last_name: User last name
        country_code: User country code (ISO 3166-1 alpha-2)
        locale: User locale (e.g., en-US)
        status: User status (active, inactive, suspended)
        email_verified: Email verification status
        phone_verified: Phone verification status
        two_factor_enabled: Two-factor authentication status
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=True,
    )
    locale: Mapped[str] = mapped_column(
        String(10),
        default="en-US",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    phone_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    # Note: Additional models like Profile, Device, etc. can be added as needed
    # profiles = relationship(
    #     "Profile", back_populates="user", cascade="all, delete-orphan"
    # )
    # devices = relationship(
    #     "Device", back_populates="user", cascade="all, delete-orphan"
    # )
    # orders = relationship(
    #     "Order", back_populates="user", cascade="all, delete-orphan"
    # )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, status={self.status})>"
