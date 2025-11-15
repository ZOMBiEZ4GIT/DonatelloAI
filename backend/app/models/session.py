"""
╔════════════════════════════════════════════════════════╗
║            User Session Database Model                  ║
║         Token Tracking & Revocation                    ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Tracks active user sessions for security
    - Enables token revocation for compromised accounts
    - Supports concurrent session limits
    - Audit trail for login activity

Security Considerations:
    - Refresh tokens hashed before storage (never plaintext)
    - Session revocation immediately invalidates tokens
    - Device fingerprinting for anomaly detection
    - IP address tracking for geographic analysis

ISO 27001 Controls:
    - A.9.4.2: Secure log-on procedures
    - A.9.4.3: Password management system
    - A.12.4.1: Event logging
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserSession(Base):
    """
    User session model for tracking active authentication sessions.

    Business Rules:
        - One refresh token per session
        - Sessions expire after configured period (default: 7 days)
        - Revoked sessions immediately invalidated
        - Device info tracked for security monitoring
        - IP address logged for geo-fencing

    Security:
        - Refresh tokens hashed with bcrypt before storage
        - Token rotation on every refresh (one-time use)
        - Automatic cleanup of expired sessions
        - Concurrent session limits enforced

    ISO 27001 Control: A.9.4.2 - Secure log-on procedures
    """

    __tablename__ = "user_sessions"

    # ┌─────────────────────────────────────────────────────────┐
    # │ Primary Identity                                         │
    # └─────────────────────────────────────────────────────────┘
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Session ID"
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this session"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Token Management (🔒 SECURITY CRITICAL)                 │
    # └─────────────────────────────────────────────────────────┘
    refresh_token_hash = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Hashed refresh token (bcrypt)"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Device & Location Information                           │
    # └─────────────────────────────────────────────────────────┘
    device_info = Column(
        JSONB,
        nullable=True,
        comment="Device information (user agent, OS, browser)"
    )
    # Example:
    # {
    #   "user_agent": "Mozilla/5.0...",
    #   "browser": "Chrome 120.0",
    #   "os": "Windows 10",
    #   "device_type": "desktop",
    #   "device_fingerprint": "hash..."
    # }

    ip_address = Column(
        String(45),  # IPv6 max length
        nullable=True,
        index=True,
        comment="IP address when session created"
    )

    last_used_ip = Column(
        String(45),
        nullable=True,
        comment="IP address of last token refresh"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Session Lifecycle                                       │
    # └─────────────────────────────────────────────────────────┘
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Session creation timestamp (UTC)"
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Session expiration timestamp (UTC)"
    )

    last_used_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Last time session was used (token refresh)"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Revocation Management                                   │
    # └─────────────────────────────────────────────────────────┘
    revoked = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Session revoked (immediately invalidated)"
    )

    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when session was revoked"
    )

    revoked_reason = Column(
        String(255),
        nullable=True,
        comment="Reason for revocation (security, logout, admin action)"
    )

    # ┌─────────────────────────────────────────────────────────┐
    # │ Relationships                                           │
    # └─────────────────────────────────────────────────────────┘
    # user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserSession(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if session is valid (not revoked and not expired)."""
        return not self.revoked and not self.is_expired

    def revoke(self, reason: str = "user_logout") -> None:
        """
        Revoke this session.

        Args:
            reason: Reason for revocation

        Security:
            - Immediately invalidates all tokens for this session
            - Triggers audit log entry
            - Cannot be undone
        """
        self.revoked = True
        self.revoked_at = datetime.utcnow()
        self.revoked_reason = reason


# ⚠️  SESSION SECURITY NOTES:
#
# 🔒 Token Storage:
# - Refresh tokens NEVER stored in plaintext
# - Hashed with bcrypt (cost factor 12)
# - Rainbow table attacks prevented
# - Salt unique per token
#
# 🔄 Token Rotation:
# - Refresh token rotated on every use
# - Old token immediately invalidated
# - Prevents token replay attacks
# - One-time use pattern enforced
#
# 🚨 Revocation:
# - Manual logout revokes session
# - Password change revokes all sessions
# - Admin can revoke user's sessions
# - Suspicious activity triggers auto-revocation
#
# 📊 Concurrent Sessions:
# - Configurable limit per user (default: 1)
# - Oldest session revoked when limit exceeded
# - Different devices tracked separately
# - Mobile vs desktop vs API sessions
#
# 🌍 IP Tracking:
# - Initial IP logged at creation
# - Last used IP updated on refresh
# - Geographic anomalies detected
# - VPN usage flagged for review
#
# 🧹 Cleanup:
# - Expired sessions deleted after 30 days
# - Revoked sessions deleted after 90 days
# - Active session count monitored
# - Database growth managed
#
# 📋 ISO 27001 Control Mapping:
# - A.9.4.2: Secure log-on procedures
# - A.9.4.3: Password management system
# - A.12.4.1: Event logging
# - A.16.1.7: Collection of evidence
