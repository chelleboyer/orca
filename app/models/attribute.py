from sqlalchemy import Integer, String, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum
import uuid
from typing import Optional, List as PyList, TYPE_CHECKING

from .base import BaseModel

if TYPE_CHECKING:
    from .project import Project
    from .object import Object


class AttributeType(enum.Enum):
    """Supported attribute data types"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    REFERENCE = "reference"
    LIST = "list"


class Attribute(BaseModel):
    """Attributes define properties that can be assigned to objects"""
    __tablename__ = "attributes"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_type: Mapped[AttributeType] = mapped_column(SQLEnum(AttributeType), nullable=False, default=AttributeType.TEXT)
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reference_object_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("objects.id"), nullable=True)
    list_options: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string for list options
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Foreign key to project (inherited from PRD requirements)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="attributes")
    reference_object: Mapped[Optional["Object"]] = relationship("Object", foreign_keys=[reference_object_id])
    object_attributes: Mapped[PyList["ObjectAttribute"]] = relationship("ObjectAttribute", back_populates="attribute", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Attribute(id={self.id}, name='{self.name}', type='{self.data_type.value}', is_core={self.is_core})>"

    @property
    def display_type(self) -> str:
        """Human-readable data type display"""
        type_display = {
            AttributeType.TEXT: "Text",
            AttributeType.NUMBER: "Number", 
            AttributeType.DATE: "Date",
            AttributeType.BOOLEAN: "Boolean",
            AttributeType.REFERENCE: "Reference",
            AttributeType.LIST: "List"
        }
        return type_display.get(self.data_type, self.data_type.value)


class ObjectAttribute(BaseModel):
    """Junction table for object-attribute relationships with values"""
    __tablename__ = "object_attributes"

    object_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("objects.id"), nullable=False)
    attribute_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("attributes.id"), nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Store all values as text, convert based on attribute type

    # Relationships
    object: Mapped["Object"] = relationship("Object", back_populates="object_attributes")
    attribute: Mapped["Attribute"] = relationship("Attribute", back_populates="object_attributes")

    def __repr__(self):
        return f"<ObjectAttribute(object_id={self.object_id}, attribute_id={self.attribute_id}, value='{self.value}')>"

    @property
    def typed_value(self):
        """Convert stored text value to appropriate Python type based on attribute type"""
        if not self.value:
            return None
            
        try:
            if self.attribute.data_type == AttributeType.NUMBER:
                # Try int first, then float
                if '.' in self.value:
                    return float(self.value)
                return int(self.value)
            elif self.attribute.data_type == AttributeType.BOOLEAN:
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.attribute.data_type == AttributeType.DATE:
                # Return as string for now, can be enhanced with datetime parsing
                return self.value
            elif self.attribute.data_type == AttributeType.REFERENCE:
                # Return the referenced object ID
                try:
                    return uuid.UUID(self.value)
                except ValueError:
                    return None
            elif self.attribute.data_type == AttributeType.LIST:
                # For list types, value should be one of the predefined options
                return self.value
            else:  # TEXT
                return self.value
        except (ValueError, AttributeError):
            return self.value
