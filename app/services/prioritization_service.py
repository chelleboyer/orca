"""
Prioritization Service

Handles Now/Next/Later prioritization for objects, CTAs, attributes, and relationships.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import json

from app.models.prioritization import (
    Prioritization, PrioritizationSnapshot,
    PriorityPhase, ItemType
)
from app.models.object import Object
from app.models.cta import CTA
from app.models.attribute import Attribute
from app.models.relationship import Relationship
from app.schemas.prioritization import (
    PrioritizationCreate, PrioritizationUpdate,
    PrioritizationSnapshotCreate, BulkPrioritizationUpdate
)


class PrioritizationService:
    """Service for managing Now/Next/Later prioritization."""

    def __init__(self, db: Session):
        self.db = db

    def create_prioritization(
        self, project_id: str, prioritization_data: PrioritizationCreate
    ) -> Prioritization:
        """Create a new prioritization."""
        # Check if prioritization already exists for this item
        existing = self.db.query(Prioritization).filter(
            and_(
                Prioritization.project_id == project_id,
                Prioritization.item_type == prioritization_data.item_type.value,
                Prioritization.item_id == prioritization_data.item_id
            )
        ).first()

        if existing:
            raise ValueError(
                f"Prioritization already exists for "
                f"{prioritization_data.item_type.value} "
                f"{prioritization_data.item_id}"
            )

        # Verify the item exists
        if not self._item_exists(
            prioritization_data.item_type,
            prioritization_data.item_id,
            project_id
        ):
            raise ValueError(
                f"{prioritization_data.item_type.value.title()} "
                f"{prioritization_data.item_id} not found in project "
                f"{project_id}"
            )

        # Get next position for the phase
        position = self._get_next_position(
            project_id,
            prioritization_data.priority_phase
        )

        # Create prioritization
        prioritization = Prioritization(
            project_id=project_id,
            item_type=prioritization_data.item_type.value,
            item_id=prioritization_data.item_id,
            priority_phase=prioritization_data.priority_phase.value,
            score=prioritization_data.score,
            position=position,
            notes=prioritization_data.notes,
            assigned_by=prioritization_data.assigned_by
        )

        self.db.add(prioritization)
        self.db.commit()
        self.db.refresh(prioritization)

        return prioritization

    def get_prioritization(
        self, project_id: str, prioritization_id: str
    ) -> Optional[Prioritization]:
        """Get a prioritization by ID."""
        return self.db.query(Prioritization).filter(
            and_(
                Prioritization.id == prioritization_id,
                Prioritization.project_id == project_id
            )
        ).first()

    def update_prioritization(
        self,
        project_id: str,
        prioritization_id: str,
        update_data: PrioritizationUpdate
    ) -> Optional[Prioritization]:
        """Update a prioritization."""
        prioritization = self.get_prioritization(project_id, prioritization_id)
        if not prioritization:
            return None

        # Update priority phase and position if changed
        if (update_data.priority_phase and
                update_data.priority_phase.value != prioritization.priority_phase):
            new_position = self._get_next_position(
                project_id,
                update_data.priority_phase
            )
            prioritization.priority_phase = update_data.priority_phase.value
            prioritization.position = new_position

        # Update other fields
        if update_data.score is not None:
            prioritization.score = update_data.score

        if update_data.position is not None:
            prioritization.position = update_data.position

        if update_data.notes is not None:
            prioritization.notes = update_data.notes

        self.db.commit()
        self.db.refresh(prioritization)

        return prioritization

    def delete_prioritization(
        self, project_id: str, prioritization_id: str
    ) -> bool:
        """Delete a prioritization."""
        prioritization = self.get_prioritization(project_id, prioritization_id)
        if not prioritization:
            return False

        self.db.delete(prioritization)
        self.db.commit()
        return True

    def get_prioritizations(
        self,
        project_id: str,
        item_type: Optional[ItemType] = None,
        priority_phase: Optional[PriorityPhase] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Prioritization]:
        """Get prioritizations with optional filtering."""
        query = self.db.query(Prioritization).filter(
            Prioritization.project_id == project_id
        )

        if item_type:
            query = query.filter(
                Prioritization.item_type == item_type.value
            )

        if priority_phase:
            query = query.filter(
                Prioritization.priority_phase == priority_phase.value
            )

        return (
            query
            .order_by(Prioritization.priority_phase, Prioritization.position)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def bulk_update_prioritizations(
        self,
        project_id: str,
        bulk_update: BulkPrioritizationUpdate
    ) -> List[Prioritization]:
        """Bulk update prioritizations (for drag-and-drop operations)."""
        updated_prioritizations = []

        for update_item in bulk_update.updates:
            item_id = update_item.get('item_id')
            item_type = update_item.get('item_type')

            if not item_id or not item_type:
                continue

            # Find existing prioritization or create new one
            prioritization = self.db.query(Prioritization).filter(
                and_(
                    Prioritization.project_id == project_id,
                    Prioritization.item_type == item_type,
                    Prioritization.item_id == item_id
                )
            ).first()

            if not prioritization:
                # Create new prioritization
                prioritization = Prioritization(
                    project_id=project_id,
                    item_type=item_type,
                    item_id=item_id,
                    priority_phase=update_item.get(
                        'priority_phase',
                        PriorityPhase.UNASSIGNED.value
                    ),
                    position=update_item.get('position', 0),
                    score=update_item.get('score')
                )
                self.db.add(prioritization)
            else:
                # Update existing prioritization
                if 'priority_phase' in update_item:
                    prioritization.priority_phase = PriorityPhase(
                        update_item['priority_phase']
                    ).value
                if 'position' in update_item:
                    prioritization.position = update_item['position']
                if 'score' in update_item:
                    prioritization.score = update_item['score']

            updated_prioritizations.append(prioritization)

        self.db.commit()

        # Refresh all updated prioritizations
        for prioritization in updated_prioritizations:
            self.db.refresh(prioritization)

        return updated_prioritizations

    def get_prioritization_board(
        self, project_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get prioritization board organized by phases."""
        prioritizations = self.get_prioritizations(project_id)

        board = {
            PriorityPhase.NOW.value: [],
            PriorityPhase.NEXT.value: [],
            PriorityPhase.LATER.value: [],
            PriorityPhase.UNASSIGNED.value: []
        }

        # Organize prioritizations by phase
        for prioritization in prioritizations:
            phase = prioritization.priority_phase
            board[phase].append(self._prioritization_to_dict(prioritization))

        # Add unassigned items
        unassigned_items = self._get_unassigned_items(project_id)
        board[PriorityPhase.UNASSIGNED.value].extend(unassigned_items)

        return board

    def get_prioritization_stats(self, project_id: str) -> Dict[str, Any]:
        """Get prioritization statistics."""
        # Get all prioritizations
        prioritizations = self.get_prioritizations(project_id)

        # Count by phase
        phase_counts = {phase.value: 0 for phase in PriorityPhase}
        item_type_stats = {}
        total_score = 0
        scored_items = 0

        for prioritization in prioritizations:
            phase_counts[prioritization.priority_phase] += 1

            # Track by item type
            item_type = prioritization.item_type
            if item_type not in item_type_stats:
                item_type_stats[item_type] = {
                    phase.value: 0 for phase in PriorityPhase
                }

            item_type_stats[item_type][prioritization.priority_phase] += 1

            # Score statistics
            if prioritization.score:
                total_score += prioritization.score
                scored_items += 1

        # Get total items in project
        total_items = self._get_total_items_count(project_id)

        return {
            'total_items': total_items,
            'prioritized_items': len(prioritizations),
            'now_count': phase_counts[PriorityPhase.NOW.value],
            'next_count': phase_counts[PriorityPhase.NEXT.value],
            'later_count': phase_counts[PriorityPhase.LATER.value],
            'unassigned_count': total_items - len(prioritizations),
            'by_item_type': item_type_stats,
            'average_score': (
                total_score / scored_items if scored_items > 0 else None
            ),
            'scored_items': scored_items
        }

    def create_snapshot(
        self,
        project_id: str,
        snapshot_data: PrioritizationSnapshotCreate
    ) -> PrioritizationSnapshot:
        """Create a prioritization snapshot."""
        # Get current prioritizations
        prioritizations = self.get_prioritizations(project_id)

        # Convert to serializable format
        snapshot_content = []
        for prioritization in prioritizations:
            snapshot_content.append({
                'id': str(prioritization.id),
                'item_type': prioritization.item_type,
                'item_id': prioritization.item_id,
                'priority_phase': prioritization.priority_phase,
                'score': prioritization.score,
                'position': prioritization.position,
                'notes': prioritization.notes,
                'assigned_by': prioritization.assigned_by,
                'assigned_at': (
                    prioritization.assigned_at.isoformat()
                    if prioritization.assigned_at else None
                )
            })

        # Create snapshot
        snapshot = PrioritizationSnapshot(
            project_id=project_id,
            snapshot_name=snapshot_data.snapshot_name,
            description=snapshot_data.description,
            snapshot_data=json.dumps(snapshot_content),
            created_by=snapshot_data.created_by
        )

        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)

        return snapshot

    def get_snapshots(self, project_id: str) -> List[PrioritizationSnapshot]:
        """Get all snapshots for a project."""
        return self.db.query(PrioritizationSnapshot).filter(
            PrioritizationSnapshot.project_id == project_id
        ).order_by(desc(PrioritizationSnapshot.created_at)).all()

    def _get_next_position(
        self, project_id: str, phase: PriorityPhase
    ) -> int:
        """Get the next position number for a phase."""
        max_position = self.db.query(Prioritization.position).filter(
            and_(
                Prioritization.project_id == project_id,
                Prioritization.priority_phase == phase.value
            )
        ).order_by(desc(Prioritization.position)).first()

        return (max_position[0] + 1) if max_position and max_position[0] else 0

    def _item_exists(
        self, item_type: ItemType, item_id: str, project_id: str
    ) -> bool:
        """Check if an item exists in the project."""
        if item_type == ItemType.OBJECT:
            return self.db.query(Object).filter(
                and_(Object.id == item_id, Object.project_id == project_id)
            ).first() is not None

        elif item_type == ItemType.CTA:
            return self.db.query(CTA).filter(
                and_(CTA.id == item_id, CTA.project_id == project_id)
            ).first() is not None

        elif item_type == ItemType.ATTRIBUTE:
            return self.db.query(Attribute).filter(
                and_(Attribute.id == item_id, Attribute.project_id == project_id)
            ).first() is not None

        elif item_type == ItemType.RELATIONSHIP:
            return self.db.query(Relationship).filter(
                and_(Relationship.id == item_id, Relationship.project_id == project_id)
            ).first() is not None

        return False

    def _prioritization_to_dict(
        self, prioritization: Prioritization
    ) -> Dict[str, Any]:
        """Convert prioritization to dictionary with item details."""
        item_details = self._get_item_details(
            prioritization.item_type,
            prioritization.item_id
        )

        return {
            'id': str(prioritization.id),
            'project_id': str(prioritization.project_id),
            'item_type': prioritization.item_type,
            'item_id': prioritization.item_id,
            'priority_phase': prioritization.priority_phase,
            'score': prioritization.score,
            'position': prioritization.position,
            'notes': prioritization.notes,
            'assigned_by': prioritization.assigned_by,
            'assigned_at': prioritization.assigned_at,
            'updated_at': prioritization.updated_at,
            'item_name': item_details.get('name'),
            'item_description': item_details.get('description')
        }

    def _get_item_details(self, item_type: str, item_id: str) -> Dict[str, Any]:
        """Get item name and description."""
        if item_type == ItemType.OBJECT.value:
            obj = self.db.query(Object).filter(Object.id == item_id).first()
            return (
                {'name': obj.name, 'description': obj.definition}
                if obj else {}
            )

        elif item_type == ItemType.CTA.value:
            cta = self.db.query(CTA).filter(CTA.id == item_id).first()
            return (
                {'name': cta.name, 'description': cta.trigger}
                if cta else {}
            )

        elif item_type == ItemType.ATTRIBUTE.value:
            attr = self.db.query(Attribute).filter(
                Attribute.id == item_id
            ).first()
            return (
                {'name': attr.name, 'description': attr.description}
                if attr else {}
            )

        elif item_type == ItemType.RELATIONSHIP.value:
            rel = self.db.query(Relationship).filter(
                Relationship.id == item_id
            ).first()
            return (
                {'name': f"{rel.name}", 'description': rel.description}
                if rel else {}
            )

        return {}

    def _get_unassigned_items(
        self, project_id: str
    ) -> List[Dict[str, Any]]:
        """Get items that don't have prioritizations."""
        unassigned = []

        # Get prioritized item IDs
        prioritized_objects = {
            p.item_id for p in self.db.query(Prioritization).filter(
                and_(
                    Prioritization.project_id == project_id,
                    Prioritization.item_type == ItemType.OBJECT.value
                )
            ).all()
        }

        prioritized_ctas = {
            p.item_id for p in self.db.query(Prioritization).filter(
                and_(
                    Prioritization.project_id == project_id,
                    Prioritization.item_type == ItemType.CTA.value
                )
            ).all()
        }

        prioritized_attributes = {
            p.item_id for p in self.db.query(Prioritization).filter(
                and_(
                    Prioritization.project_id == project_id,
                    Prioritization.item_type == ItemType.ATTRIBUTE.value
                )
            ).all()
        }

        prioritized_relationships = {
            p.item_id for p in self.db.query(Prioritization).filter(
                and_(
                    Prioritization.project_id == project_id,
                    Prioritization.item_type == ItemType.RELATIONSHIP.value
                )
            ).all()
        }

        # Add unassigned objects
        objects = self.db.query(Object).filter(
            Object.project_id == project_id
        ).all()
        for obj in objects:
            if str(obj.id) not in prioritized_objects:
                unassigned.append({
                    'item_type': ItemType.OBJECT.value,
                    'item_id': str(obj.id),
                    'item_name': obj.name,
                    'item_description': obj.definition,
                    'priority_phase': PriorityPhase.UNASSIGNED.value
                })

        # Add unassigned CTAs
        ctas = self.db.query(CTA).filter(
            CTA.project_id == project_id
        ).all()
        for cta in ctas:
            if str(cta.id) not in prioritized_ctas:
                unassigned.append({
                    'item_type': ItemType.CTA.value,
                    'item_id': str(cta.id),
                    'item_name': cta.name,
                    'item_description': cta.trigger,
                    'priority_phase': PriorityPhase.UNASSIGNED.value
                })

        # Add unassigned attributes
        attributes = self.db.query(Attribute).filter(
            Attribute.project_id == project_id
        ).all()
        for attr in attributes:
            if str(attr.id) not in prioritized_attributes:
                unassigned.append({
                    'item_type': ItemType.ATTRIBUTE.value,
                    'item_id': str(attr.id),
                    'item_name': attr.name,
                    'item_description': attr.description,
                    'priority_phase': PriorityPhase.UNASSIGNED.value
                })

        # Add unassigned relationships
        relationships = self.db.query(Relationship).filter(
            Relationship.project_id == project_id
        ).all()
        for rel in relationships:
            if str(rel.id) not in prioritized_relationships:
                unassigned.append({
                    'item_type': ItemType.RELATIONSHIP.value,
                    'item_id': str(rel.id),
                    'item_name': rel.name,
                    'item_description': rel.description,
                    'priority_phase': PriorityPhase.UNASSIGNED.value
                })

        return unassigned

    def _get_total_items_count(self, project_id: str) -> int:
        """Get total count of all items in project."""
        object_count = self.db.query(Object).filter(
            Object.project_id == project_id
        ).count()
        cta_count = self.db.query(CTA).filter(
            CTA.project_id == project_id
        ).count()
        attribute_count = self.db.query(Attribute).filter(
            Attribute.project_id == project_id
        ).count()
        relationship_count = self.db.query(Relationship).filter(
            Relationship.project_id == project_id
        ).count()

        return object_count + cta_count + attribute_count + relationship_count
