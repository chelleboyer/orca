"""
Base model classes with common fields and utilities
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )


class UUIDMixin:
    """Mixin to add UUID primary key to models"""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4, 
        index=True
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Base model class with UUID primary key and timestamps
    Abstract base class for all models
    """
    
    __abstract__ = True


def generate_slug(title: str, max_length: int = 120) -> str:
    """
    Generate a URL-friendly slug from a title
    
    Args:
        title: The title to convert to a slug
        max_length: Maximum length of the slug
        
    Returns:
        URL-friendly slug
    """
    import re
    
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special characters
    slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces and multiple hyphens
    slug = slug.strip('-')                # Remove leading/trailing hyphens
    
    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug or 'untitled'


def generate_unique_slug(base_slug: str, check_function, max_length: int = 120) -> str:
    """
    Generate a unique slug by appending numbers if conflicts exist
    
    Args:
        base_slug: The base slug to make unique
        check_function: Function that checks if slug exists (returns True if exists)
        max_length: Maximum length of the slug
        
    Returns:
        Unique slug
    """
    if not check_function(base_slug):
        return base_slug
    
    # Try appending numbers
    counter = 1
    while counter < 1000:  # Prevent infinite loops
        # Reserve space for suffix
        suffix = f"-{counter}"
        max_base_length = max_length - len(suffix)
        
        if max_base_length > 0:
            test_slug = base_slug[:max_base_length] + suffix
            if not check_function(test_slug):
                return test_slug
        
        counter += 1
    
    # Fallback to UUID suffix if too many conflicts
    uuid_suffix = f"-{uuid.uuid4().hex[:8]}"
    max_base_length = max_length - len(uuid_suffix)
    return base_slug[:max_base_length] + uuid_suffix
