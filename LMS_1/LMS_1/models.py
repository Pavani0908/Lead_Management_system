"""
SQLAlchemy models for the Lead Management System.

This module defines the Lead entity and status values stored in SQLite.
"""

from __future__ import annotations

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

# Shared SQLAlchemy instance — bound to the Flask app in app.py
db = SQLAlchemy()


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime (SQLite stores naive; we normalize in app)."""
    return datetime.now(timezone.utc)


class Lead(db.Model):
    """
    A sales / inquiry lead captured from the public form.

    status must be one of: New, Contacted, Closed
    """

    __tablename__ = "leads"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(40), nullable=False)
    business_type = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="New", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Allowed status labels (kept as strings for simple JSON + SQLite)
    STATUS_NEW = "New"
    STATUS_CONTACTED = "Contacted"
    STATUS_CLOSED = "Closed"
    ALLOWED_STATUSES = (STATUS_NEW, STATUS_CONTACTED, STATUS_CLOSED)

    def to_dict(self) -> dict:
        """Serialize lead for JSON APIs."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "business_type": self.business_type,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Lead {self.id} {self.email} {self.status}>"
