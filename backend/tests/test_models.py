"""
Tests for database models.
"""

import pytest
from datetime import datetime

from app.models.user import User, UserRole, UserStatus
from app.models.department import Department
from app.models.generation import Generation, GenerationStatus, ModelProvider


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self):
        """Test user instance creation."""
        user = User(
            azure_ad_object_id="test-uuid",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            display_name="Test User",
            role=UserRole.STANDARD_USER,
        )

        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.STANDARD_USER

    def test_mfa_enforcement(self):
        """Test MFA enforcement logic."""
        user = User(
            azure_ad_object_id="test-uuid",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            display_name="Test User",
            mfa_enabled=False,
        )

        # User without MFA should require enforcement
        assert user.requires_mfa_enforcement(grace_period_days=7)

        # User with MFA enabled should not require enforcement
        user.mfa_enabled = True
        assert not user.requires_mfa_enforcement()


class TestDepartmentModel:
    """Tests for Department model."""

    def test_department_creation(self):
        """Test department instance creation."""
        dept = Department(
            name="Engineering",
            code="ENG",
            monthly_budget_aud=10000.00,
        )

        assert dept.name == "Engineering"
        assert dept.code == "ENG"
        assert dept.monthly_budget_aud == 10000.00


class TestGenerationModel:
    """Tests for Generation model."""

    def test_generation_creation(self):
        """Test generation instance creation."""
        gen = Generation(
            request_id="test-uuid",
            user_id=1,
            status=GenerationStatus.PENDING,
            prompt="A beautiful sunset",
            model_provider=ModelProvider.DALLE3,
            cost_aud=0.08,
        )

        assert gen.request_id == "test-uuid"
        assert gen.status == GenerationStatus.PENDING
        assert gen.prompt == "A beautiful sunset"

    def test_generation_is_complete(self):
        """Test generation completion status."""
        gen = Generation(
            request_id="test-uuid",
            user_id=1,
            status=GenerationStatus.COMPLETED,
            prompt="Test",
            model_provider=ModelProvider.DALLE3,
        )

        assert gen.is_complete

        gen.status = GenerationStatus.PROCESSING
        assert not gen.is_complete
