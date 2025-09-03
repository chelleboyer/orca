"""
Object Cards service for managing card-based object display
Aggregates object data with attributes, relationships, and completion status
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from dataclasses import dataclass

from app.models.object import Object
from app.models.attribute import Attribute, ObjectAttribute
from app.services.object_service import ObjectService
from app.services.attribute_service import AttributeService


@dataclass
class ObjectCardData:
    """Data structure for object card display"""
    id: str
    name: str
    definition: str
    definition_summary: str
    core_attributes: List[Dict[str, Any]]
    all_attributes_count: int
    relationship_count: int
    completion_status: Dict[str, bool]
    quick_actions: List[str]
    created_at: str
    updated_at: str


@dataclass
class CardFilterParams:
    """Parameters for filtering object cards"""
    query: Optional[str] = None
    has_definition: Optional[bool] = None
    has_attributes: Optional[bool] = None
    has_relationships: Optional[bool] = None
    has_core_attributes: Optional[bool] = None
    attribute_type: Optional[str] = None
    min_attributes: Optional[int] = None
    max_attributes: Optional[int] = None
    layout: str = "grid"  # "grid" or "list"
    sort_by: str = "name"  # "name", "created_at", "updated_at", "definition", "attributes", "relationships"
    sort_order: str = "asc"
    limit: int = 20
    offset: int = 0


class ObjectCardsService:
    """Service for managing object card display and filtering"""

    def __init__(self, db: Session):
        self.db = db
        self.object_service = ObjectService(db)
        self.attribute_service = AttributeService(db)

    def get_objects_with_card_data(
        self,
        project_id: str,
        filters: CardFilterParams
    ) -> Tuple[List[ObjectCardData], int]:
        """
        Get objects with aggregated card data for display

        Args:
            project_id: UUID of the project
            filters: Filter parameters for objects

        Returns:
            Tuple of (object cards list, total count)
        """
        # Build base query with eager loading
        query = self.db.query(Object).filter(Object.project_id == project_id)
        query = query.options(
            joinedload(Object.object_attributes).joinedload(ObjectAttribute.attribute),
            joinedload(Object.outgoing_relationships),
            joinedload(Object.incoming_relationships)
        )

        # Apply text search filter
        if filters.query:
            search_term = f"%{filters.query}%"
            query = query.filter(
                or_(
                    Object.name.ilike(search_term),
                    Object.definition.ilike(search_term)
                )
            )

        # Apply completion status filters
        if filters.has_definition is not None:
            if filters.has_definition:
                query = query.filter(Object.definition.isnot(None))
                query = query.filter(Object.definition != "")
            else:
                query = query.filter(
                    or_(Object.definition.is_(None), Object.definition == "")
                )

        if filters.has_attributes is not None:
            # Filter objects with/without attributes
            if filters.has_attributes:
                query = query.filter(Object.object_attributes.any())
            else:
                query = query.filter(~Object.object_attributes.any())

        if filters.has_core_attributes is not None:
            # Filter objects with/without core attributes
            if filters.has_core_attributes:
                query = query.filter(
                    Object.object_attributes.any(
                        ObjectAttribute.attribute.has(Attribute.is_core .is_(True))
                    )
                )
            else:
                query = query.filter(
                    ~Object.object_attributes.any(
                        ObjectAttribute.attribute.has(Attribute.is_core .is_(True))
                    )
                )

        if filters.has_relationships is not None:
            # Filter objects with/without relationships
            if filters.has_relationships:
                query = query.filter(
                    or_(
                        Object.outgoing_relationships.any(),
                        Object.incoming_relationships.any()
                    )
                )
            else:
                query = query.filter(
                    and_(
                        ~Object.outgoing_relationships.any(),
                        ~Object.incoming_relationships.any()
                    )
                )

        # Apply attribute count filters
        if filters.min_attributes is not None or filters.max_attributes is not None:
            # Subquery to count attributes per object
            attr_count_subq = (
                self.db.query(
                    ObjectAttribute.object_id,
                    func.count(ObjectAttribute.id).label('attr_count')
                )
                .group_by(ObjectAttribute.object_id)
                .subquery()
            )

            query = query.outerjoin(attr_count_subq, Object.id == attr_count_subq.c.object_id)

            if filters.min_attributes is not None:
                query = query.filter(
                    func.coalesce(attr_count_subq.c.attr_count, 0) >= filters.min_attributes
                )

            if filters.max_attributes is not None:
                query = query.filter(
                    func.coalesce(attr_count_subq.c.attr_count, 0) <= filters.max_attributes
                )

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        if filters.sort_by == "name":
            sort_col = Object.name
        elif filters.sort_by == "created_at":
            sort_col = Object.created_at
        elif filters.sort_by == "updated_at":
            sort_col = Object.updated_at
        elif filters.sort_by == "definition":
            sort_col = Object.definition
        else:
            sort_col = Object.name  # Default fallback

        if filters.sort_order == "desc":
            query = query.order_by(desc(sort_col))
        else:
            query = query.order_by(asc(sort_col))

        # Apply pagination
        objects = query.offset(filters.offset).limit(filters.limit).all()

        # Transform to card data
        card_data = []
        for obj in objects:
            card_data.append(self._object_to_card_data(obj))

        return card_data, total

    def get_single_object_card(self, project_id: str, object_id: str) -> Optional[ObjectCardData]:
        """
        Get single object card data

        Args:
            project_id: UUID of the project
            object_id: UUID of the object

        Returns:
            Object card data or None if not found
        """
        obj = (
            self.db.query(Object)
            .filter(and_(Object.id == object_id, Object.project_id == project_id))
            .options(
                joinedload(Object.object_attributes).joinedload(ObjectAttribute.attribute),
                joinedload(Object.outgoing_relationships),
                joinedload(Object.incoming_relationships)
            )
            .first()
        )

        if not obj:
            return None

        return self._object_to_card_data(obj)

    def _object_to_card_data(self, obj: Object) -> ObjectCardData:
        """
        Transform Object model to ObjectCardData

        Args:
            obj: Object model instance

        Returns:
            ObjectCardData for card display
        """
        # Core attributes (marked as core=True)
        core_attributes = []
        all_attributes_count = len(obj.object_attributes)

        for obj_attr in obj.object_attributes:
            if obj_attr.attribute.is_core:
                core_attributes.append({
                    "id": str(obj_attr.attribute.id),
                    "name": obj_attr.attribute.name,
                    "data_type": obj_attr.attribute.data_type.value,
                    "display_type": self._get_attribute_display_type(obj_attr.attribute.data_type.value),
                    "value": obj_attr.value,
                    "is_core": True
                })

        # Sort core attributes by name
        core_attributes.sort(key=lambda x: x["name"])

        # Count relationships
        relationship_count = len(obj.outgoing_relationships) + len(obj.incoming_relationships)

        # Calculate completion status
        completion_status = {
            "has_definition": bool(getattr(obj, 'definition') and str(getattr(obj, 'definition')).strip()),
            "has_attributes": all_attributes_count > 0,
            "has_core_attributes": len(core_attributes) > 0,
            "has_relationships": relationship_count > 0,
            "completion_score": self._calculate_completion_score(
                bool(getattr(obj, 'definition') and str(getattr(obj, 'definition')).strip()),
                all_attributes_count > 0,
                len(core_attributes) > 0,
                relationship_count > 0
            )
        }

        # Generate quick actions based on completion status
        quick_actions = self._generate_quick_actions(completion_status)

        # Create definition summary (truncate long definitions)
        definition_summary = self._create_definition_summary(str(getattr(obj, 'definition') or ""))

        return ObjectCardData(
            id=str(getattr(obj, 'id')),
            name=str(getattr(obj, 'name')),
            definition=str(getattr(obj, 'definition') or ""),
            definition_summary=definition_summary,
            core_attributes=core_attributes,
            all_attributes_count=all_attributes_count,
            relationship_count=relationship_count,
            completion_status=completion_status,
            quick_actions=quick_actions,
            created_at=getattr(obj, 'created_at').isoformat(),
            updated_at=getattr(obj, 'updated_at').isoformat()
        )

    def _get_attribute_display_type(self, data_type: str) -> str:
        """Get human-readable attribute type for display"""
        type_mapping = {
            "text": "Text",
            "number": "Number",
            "date": "Date",
            "boolean": "Boolean",
            "reference": "Reference",
            "list": "List"
        }
        return type_mapping.get(data_type, "Unknown")

    def _calculate_completion_score(
        self,
        has_definition: bool,
        has_attributes: bool,
        has_core_attributes: bool,
        has_relationships: bool
    ) -> float:
        """
        Calculate completion score as percentage (0-100)

        Args:
            has_definition: Object has definition
            has_attributes: Object has any attributes
            has_core_attributes: Object has core attributes
            has_relationships: Object has relationships

        Returns:
            Completion score (0.0 to 100.0)
        """
        total_points = 4
        earned_points = 0

        if has_definition:
            earned_points += 1
        if has_attributes:
            earned_points += 1
        if has_core_attributes:
            earned_points += 1
        if has_relationships:
            earned_points += 1

        return (earned_points / total_points) * 100.0

    def _generate_quick_actions(self, completion_status: Dict[str, bool]) -> List[str]:
        """
        Generate appropriate quick actions based on object completion status

        Args:
            completion_status: Object completion status

        Returns:
            List of quick action names
        """
        actions = ["view", "edit"]  # Always available

        if not completion_status["has_definition"]:
            actions.append("add_definition")

        if not completion_status["has_attributes"]:
            actions.append("add_attributes")
        elif not completion_status["has_core_attributes"]:
            actions.append("mark_core_attributes")

        if not completion_status["has_relationships"]:
            actions.append("add_relationships")

        # Add export/duplicate for complete objects
        if completion_status["completion_score"] >= 75.0:
            actions.extend(["duplicate", "export"])

        return actions

    def _create_definition_summary(self, definition: Optional[str]) -> str:
        """
        Create a short summary of the object definition for card display

        Args:
            definition: Full object definition

        Returns:
            Truncated definition summary
        """
        if not definition or not definition.strip():
            return ""

        # Truncate at 120 characters, break at word boundary
        if len(definition) <= 120:
            return definition.strip()

        truncated = definition[:120].strip()

        # Find last space to avoid cutting words
        last_space = truncated.rfind(' ')
        if last_space > 100:  # Only truncate at word if reasonable
            truncated = truncated[:last_space]

        return truncated + "..."

    def get_card_statistics(self, project_id: str) -> Dict[str, Any]:
        """
        Get statistics for object cards display

        Args:
            project_id: UUID of the project

        Returns:
            Dictionary with card statistics
        """
        # Base query
        base_query = self.db.query(Object).filter(Object.project_id == project_id)

        total_objects = base_query.count()

        # Objects with definitions
        with_definitions = base_query.filter(
            and_(Object.definition.isnot(None), Object.definition != "")
        ).count()

        # Objects with attributes
        with_attributes = base_query.filter(Object.object_attributes.any()).count()

        # Objects with core attributes
        with_core_attributes = base_query.filter(
            Object.object_attributes.any(
                ObjectAttribute.attribute.has(Attribute.is_core .is_(True))
            )
        ).count()

        # Objects with relationships
        with_relationships = base_query.filter(
            or_(
                Object.outgoing_relationships.any(),
                Object.incoming_relationships.any()
            )
        ).count()

        # Calculate completion percentages
        def safe_percentage(count: int, total: int) -> float:
            return (count / total * 100.0) if total > 0 else 0.0

        return {
            "total_objects": total_objects,
            "with_definitions": with_definitions,
            "with_attributes": with_attributes,
            "with_core_attributes": with_core_attributes,
            "with_relationships": with_relationships,
            "completion_percentages": {
                "definitions": safe_percentage(with_definitions, total_objects),
                "attributes": safe_percentage(with_attributes, total_objects),
                "core_attributes": safe_percentage(with_core_attributes, total_objects),
                "relationships": safe_percentage(with_relationships, total_objects)
            },
            "average_completion": safe_percentage(
                with_definitions + with_attributes + with_core_attributes + with_relationships,
                total_objects * 4  # 4 completion criteria
            )
        }
