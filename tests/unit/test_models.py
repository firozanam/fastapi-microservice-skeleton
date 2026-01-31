"""
Unit tests for models module.
Tests BaseModel and User model.
"""
import pytest
from uuid import UUID, uuid4

from app.models.base import BaseModel, TimestampMixin, UUIDMixin
from app.models.user import User


@pytest.mark.unit
class TestBaseModel:
    """Test BaseModel class."""

    def test_base_model_exists(self):
        """Test that BaseModel exists."""
        assert BaseModel is not None

    def test_base_model_is_abstract(self):
        """Test that BaseModel is abstract."""
        assert BaseModel.__abstract__ is True


@pytest.mark.unit
class TestTimestampMixin:
    """Test TimestampMixin class."""

    def test_timestamp_mixin_has_created_at(self):
        """Test that TimestampMixin has created_at field."""
        assert hasattr(TimestampMixin, "created_at")

    def test_timestamp_mixin_has_updated_at(self):
        """Test that TimestampMixin has updated_at field."""
        assert hasattr(TimestampMixin, "updated_at")


@pytest.mark.unit
class TestUUIDMixin:
    """Test UUIDMixin class."""

    def test_uuid_mixin_has_id(self):
        """Test that UUIDMixin has id field."""
        assert hasattr(UUIDMixin, "id")


@pytest.mark.unit
class TestUserModel:
    """Test User model."""

    def test_user_model_attributes(self):
        """Test that User model has all expected attributes."""
        assert hasattr(User, "email")
        assert hasattr(User, "password_hash")
        assert hasattr(User, "first_name")
        assert hasattr(User, "last_name")
        assert hasattr(User, "phone")
        assert hasattr(User, "country_code")
        assert hasattr(User, "locale")
        assert hasattr(User, "status")
        assert hasattr(User, "email_verified")
        assert hasattr(User, "phone_verified")
        assert hasattr(User, "two_factor_enabled")
        assert hasattr(User, "created_at")
        assert hasattr(User, "updated_at")

    def test_user_model_inherits_base_model(self):
        """Test that User model inherits from BaseModel."""
        assert issubclass(User, BaseModel)

    def test_user_model_inherits_timestamp_mixin(self):
        """Test that User model inherits from TimestampMixin."""
        assert issubclass(User, TimestampMixin)

    def test_user_model_inherits_uuid_mixin(self):
        """Test that User model inherits from UUIDMixin."""
        assert issubclass(User, UUIDMixin)

    def test_user_model_tablename(self):
        """Test that User model has correct tablename."""
        assert User.__tablename__ == "users"

    def test_user_model_repr(self):
        """Test that User model has __repr__ method."""
        assert hasattr(User, "__repr__")

    def test_user_repr_format(self):
        """Test User __repr__ format."""
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            status="active"
        )

        repr_str = repr(user)

        assert "User(id=" in repr_str
        assert "email=test@example.com" in repr_str
        assert "status=active" in repr_str

    def test_user_model_email_unique(self):
        """Test that User email field is unique."""
        assert User.email.property.columns[0].unique

    def test_user_model_email_indexed(self):
        """Test that User email field is indexed."""
        assert User.email.property.columns[0].index

    def test_user_model_phone_unique(self):
        """Test that User phone field is unique."""
        assert User.phone.property.columns[0].unique

    def test_user_model_phone_indexed(self):
        """Test that User phone field is indexed."""
        assert User.phone.property.columns[0].index

    def test_user_model_password_hash_required(self):
        """Test that User password_hash field is required."""
        assert User.password_hash.property.columns[0].nullable is False

    def test_user_model_first_name_required(self):
        """Test that User first_name field is required."""
        assert User.first_name.property.columns[0].nullable is False

    def test_user_model_last_name_required(self):
        """Test that User last_name field is required."""
        assert User.last_name.property.columns[0].nullable is False

    def test_user_model_country_code_nullable(self):
        """Test that User country_code field is nullable."""
        assert User.country_code.property.columns[0].nullable is True

    def test_user_model_locale_default(self):
        """Test that User locale field has default value."""
        assert User.locale.property.columns[0].default.arg == "en-US"

    def test_user_model_locale_required(self):
        """Test that User locale field is required."""
        assert User.locale.property.columns[0].nullable is False

    def test_user_model_status_default(self):
        """Test that User status field has default value."""
        assert User.status.property.columns[0].default.arg == "active"

    def test_user_model_status_required(self):
        """Test that User status field is required."""
        assert User.status.property.columns[0].nullable is False

    def test_user_model_email_verified_default(self):
        """Test that User email_verified field has default value."""
        assert User.email_verified.property.columns[0].default.arg is False

    def test_user_model_email_verified_required(self):
        """Test that User email_verified field is required."""
        assert User.email_verified.property.columns[0].nullable is False

    def test_user_model_phone_verified_default(self):
        """Test that User phone_verified field has default value."""
        assert User.phone_verified.property.columns[0].default.arg is False

    def test_user_model_phone_verified_required(self):
        """Test that User phone_verified field is required."""
        assert User.phone_verified.property.columns[0].nullable is False

    def test_user_model_two_factor_enabled_default(self):
        """Test that User two_factor_enabled field has default value."""
        assert User.two_factor_enabled.property.columns[0].default.arg is False

    def test_user_model_two_factor_enabled_required(self):
        """Test that User two_factor_enabled field is required."""
        assert User.two_factor_enabled.property.columns[0].nullable is False

    def test_user_model_to_dict(self):
        """Test that User model to_dict() method works correctly."""
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            password_hash="hashed_password",
            first_name="Test",
            last_name="User",
            status="active",
            locale="en-US"
        )
        
        # Call to_dict method
        user_dict = user.to_dict()
        
        # Verify it returns a dictionary
        assert isinstance(user_dict, dict)
        
        # Verify it contains expected keys
        assert "id" in user_dict
        assert "email" in user_dict
        assert "first_name" in user_dict
        assert "last_name" in user_dict
        assert "status" in user_dict
        
        # Verify values
        assert user_dict["email"] == "test@example.com"
        assert user_dict["first_name"] == "Test"
        assert user_dict["last_name"] == "User"
        assert user_dict["status"] == "active"
