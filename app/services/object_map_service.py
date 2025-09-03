"""
Object Map service for generating visual representation data
"""

import uuid
from typing import Dict, List, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.object import Object
from app.models.relationship import Relationship
from app.models.attribute import Attribute, ObjectAttribute
from app.models.project import Project
from app.core.exceptions import NotFoundError


class ObjectMapService:
    """Service for generating object map visualization data"""

    def __init__(self, db: Session):
        self.db = db

    def get_object_map_data(self, project_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get comprehensive object map data for visualization

        Returns:
            Dictionary with objects, relationships, and layout data
        """
        # Verify project exists
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundError("Project not found")

        # Get all objects with their core attributes
        objects = self._get_objects_with_attributes(project_id)

        # Get all relationships
        relationships = self._get_relationships_data(project_id)

        # Get layout metadata (positions, zoom level, etc.)
        layout_data = self._get_layout_data(project_id)

        # Generate statistics
        stats = self._get_map_statistics(project_id)

        return {
            "project_id": str(project_id),
            "project_title": project.title,
            "objects": objects,
            "relationships": relationships,
            "layout": layout_data,
            "statistics": stats,
            "metadata": {
                "generated_at": "2025-09-02T00:00:00Z",
                "version": "1.0"
            }
        }

    def _get_objects_with_attributes(self, project_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get all objects with their core attributes for the map"""
        objects_query = self.db.query(Object).options(
            joinedload(Object.object_attributes).joinedload(ObjectAttribute.attribute)
        ).filter(
            and_(Object.project_id == project_id, Object.is_active .is_(True))
        ).order_by(Object.name)

        objects_data = []
        for obj in objects_query.all():
            # Get core attributes for this object
            core_attributes = []
            all_attributes = []

            for obj_attr in obj.object_attributes:
                attr_data = {
                    "id": str(obj_attr.attribute.id),
                    "name": obj_attr.attribute.name,
                    "data_type": obj_attr.attribute.data_type.value,
                    "display_type": obj_attr.attribute.display_type,
                    "value": obj_attr.value,
                    "typed_value": obj_attr.typed_value,
                    "is_core": obj_attr.attribute.is_core
                }

                all_attributes.append(attr_data)

                if obj_attr.attribute.is_core:
                    core_attributes.append(attr_data)

            # Safely handle definition truncation
            definition = getattr(obj, 'definition', '') or ""
            definition_short = (definition[:100] + "...") if len(definition) > 100 else definition

            objects_data.append({
                "id": str(obj.id),
                "name": getattr(obj, 'name', ''),
                "definition": definition,
                "definition_short": definition_short,
                "core_attributes": core_attributes,
                "all_attributes": all_attributes,
                "attribute_count": len(all_attributes),
                "core_attribute_count": len(core_attributes),
                "object_type": "primary",  # Could be extended with object classification
                "position": self._get_object_position(obj.uuid),
                "created_at": obj.created_at.isoformat(),
                "updated_at": obj.updated_at.isoformat()
            })

        return objects_data

    def _get_relationships_data(self, project_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get all relationships for the map visualization"""
        relationships_query = self.db.query(Relationship).options(
            joinedload(Relationship.object_a),
            joinedload(Relationship.object_b)
        ).filter(
            and_(Relationship.project_id == project_id, Relationship.is_active .is_(True))
        ).order_by(Relationship.created_at)

        relationships_data = []
        for rel in relationships_query.all():
            relationships_data.append({
                "id": str(rel.id),
                "object_a_id": str(rel.object_a_id),
                "object_b_id": str(rel.object_b_id),
                "object_a_name": rel.object_a.name,
                "object_b_name": rel.object_b.name,
                "relationship_type": rel.relationship_type,
                "cardinality_a": rel.cardinality_a.value if rel.cardinality_a else None,
                "cardinality_b": rel.cardinality_b.value if rel.cardinality_b else None,
                "description": rel.description,
                "is_bidirectional": rel.is_bidirectional,
                "connection_points": self._get_connection_points(rel.uuid),
                "style": {
                    "line_type": "solid",  # Could be extended with different line styles
                    "color": "#666666",
                    "width": 2
                }
            })

        return relationships_data

    def _get_object_position(self, object_id: uuid.UUID) -> Dict[str, float]:
        """Get or generate position for an object in the map"""
        # For now, return default positions - this could be extended to store/retrieve
        # user-customized positions from a separate table

        # Simple grid layout as default
        object_index = hash(str(object_id)) % 100  # Simple hash for consistent positioning
        grid_size = 10

        x = (object_index % grid_size) * 250 + 100  # 250px spacing
        y = (object_index // grid_size) * 200 + 100  # 200px spacing

        return {
            "x": float(x),
            "y": float(y),
            "z": 0.0  # For future 3D support
        }

    def _get_connection_points(self, relationship_id: uuid.UUID) -> Dict[str, Any]:
        """Get connection points for relationship lines"""
        # Default connection points - could be customized based on object positions
        return {
            "start": {"side": "right", "offset": 0.5},  # Right side, middle
            "end": {"side": "left", "offset": 0.5}      # Left side, middle
        }

    def _get_layout_data(self, project_id: uuid.UUID) -> Dict[str, Any]:
        """Get layout configuration and viewport settings"""
        return {
            "viewport": {
                "zoom": 1.0,
                "center_x": 500.0,
                "center_y": 400.0,
                "min_zoom": 0.1,
                "max_zoom": 3.0
            },
            "grid": {
                "enabled": True,
                "size": 50,
                "color": "#f0f0f0"
            },
            "auto_layout": {
                "algorithm": "force_directed",  # or "hierarchical", "circular"
                "spacing": 200,
                "iterations": 100
            },
            "export_settings": {
                "formats": ["png", "svg", "pdf"],
                "default_format": "png",
                "dpi": 300
            }
        }

    def _get_map_statistics(self, project_id: uuid.UUID) -> Dict[str, Any]:
        """Get statistics about the object map"""

        # Object statistics
        object_count = self.db.query(Object).filter(
            and_(Object.project_id == project_id, Object.is_active .is_(True))
        ).count()

        # Relationship statistics
        relationship_count = self.db.query(Relationship).filter(
            and_(Relationship.project_id == project_id, Relationship.is_active .is_(True))
        ).count()

        # Attribute statistics
        attribute_count = self.db.query(Attribute).filter(
            and_(Attribute.project_id == project_id, Attribute.is_active .is_(True))
        ).count()

        core_attribute_count = self.db.query(Attribute).filter(
            and_(
                Attribute.project_id == project_id,
                Attribute.is_active .is_(True),
                Attribute.is_core .is_(True)
            )
        ).count()

        return {
            "object_count": object_count,
            "relationship_count": relationship_count,
            "attribute_count": attribute_count,
            "core_attribute_count": core_attribute_count,
            "density": relationship_count / max(object_count, 1),  # Relationships per object
            "complexity_score": self._calculate_complexity_score(object_count, relationship_count, attribute_count)
        }

    def _calculate_complexity_score(self, objects: int, relationships: int, attributes: int) -> float:
        """Calculate a complexity score for the domain model"""
        if objects == 0:
            return 0.0

        # Simple complexity formula - can be refined
        base_score = objects * 1.0
        relationship_factor = relationships * 0.5
        attribute_factor = attributes * 0.2

        total_score = base_score + relationship_factor + attribute_factor

        # Normalize to 0-100 scale
        normalized = min(100.0, (total_score / 10.0) * 100)
        return round(normalized, 1)

    def update_object_position(self, project_id: uuid.UUID, object_id: uuid.UUID, x: float, y: float) -> bool:
        """Update object position in the map (future feature)"""
        # This would store positions in a separate ObjectPosition table
        # For now, return True to indicate the interface is ready
        return True

    def auto_layout_objects(self, project_id: uuid.UUID, algorithm: str = "force_directed") -> Dict[str, Any]:
        """Apply auto-layout algorithm to arrange objects (future feature)"""
        # This would implement various layout algorithms
        # For now, return basic grid layout

        objects = self.db.query(Object).filter(
            and_(Object.project_id == project_id, Object.is_active .is_(True))
        ).all()

        positions = {}
        for i, obj in enumerate(objects):
            grid_size = 10
            x = (i % grid_size) * 250 + 100
            y = (i // grid_size) * 200 + 100
            positions[str(obj.id)] = {"x": x, "y": y}

        return {
            "algorithm": algorithm,
            "positions": positions,
            "success": True
        }

    def export_map_data(self, project_id: uuid.UUID, format: str = "json") -> Dict[str, Any]:
        """Export map data for external use"""
        map_data = self.get_object_map_data(project_id)

        if format == "json":
            return map_data
        elif format == "graphml":
            # Future: Convert to GraphML format for external tools
            return {"format": "graphml", "data": "Not implemented yet"}
        else:
            raise ValueError(f"Unsupported export format: {format}")
