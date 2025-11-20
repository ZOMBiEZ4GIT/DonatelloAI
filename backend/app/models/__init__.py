"""
╔════════════════════════════════════════════════════════╗
║              Database Models Package                    ║
║         SQLAlchemy ORM Models                          ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - All database models for the application
    - Defines schema for PostgreSQL/Azure SQL
    - Relationships between entities

ISO 27001 Control: A.12.3.1 - Information backup
"""

from app.models.base import Base
from app.models.user import User
from app.models.department import Department
from app.models.user_budget import UserBudget
from app.models.generation import Generation, GenerationStatus, ModelType
from app.models.budget import Budget, BudgetAlert

__all__ = [
    "Base",
    "User",
    "Department",
    "UserBudget",
    "Generation",
    "GenerationStatus",
    "ModelType",
    "Budget",
    "BudgetAlert",
]
