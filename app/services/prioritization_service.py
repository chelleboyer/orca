"""
Prioritization service for managing Now/Next/Later prioritization
Handles objects, CTAs, attributes, and relationships prioritization
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from fastapi import HTTPException, status
import uuid
import json

from app.models.prioritization import Prioritization, PrioritizationSnapshot, PriorityPhase, ItemType
from app.models.object import Object
from app.models.cta import CTA
from app.models.attribute import Attribute
from app.models.relationship import Relationship
from app.models.project import Project
from app.schemas.prioritization import (
    PrioritizationCreate, PrioritizationUpdate, PrioritizationFilterParams,
    PrioritizationSnapshotCreate, BulkPrioritizationUpdate
)


class PrioritizationService:
    """Service for managing prioritization operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_prioritization(self, prioritization_data: PrioritizationCreate) -> Prioritization:
        """Create a new prioritization entry"""
        
        # Check if prioritization already exists for this item
        existing = self.db.query(Prioritization).filter(
            and_(
                Prioritization.project_id == prioritization_data.project_id,
                Prioritization.item_type == prioritization_data.item_type,
                Prioritization.item_id == prioritization_data.item_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prioritization already exists for {prioritization_data.item_type.value} {prioritization_data.item_id}"
            )
        
        # Verify the item exists
        self._verify_item_exists(prioritization_data.item_type, prioritization_data.item_id)
        
        # Get next position in the phase
        next_position = self._get_next_position(
            prioritization_data.project_id, 
            prioritization_data.priority_phase
        )
        
        prioritization = Prioritization(
            project_id=prioritization_data.project_id,
            item_type=prioritization_data.item_type,
            item_id=prioritization_data.item_id,
            priority_phase=prioritization_data.priority_phase,
            score=prioritization_data.score,
            position=next_position,
            notes=prioritization_data.notes,
            assigned_by=prioritization_data.assigned_by
        )
        
        self.db.add(prioritization)
        self.db.commit()
        self.db.refresh(prioritization)
        
        return prioritization
    
    def get_prioritization(self, prioritization_id: str) -> Optional[Prioritization]:
        """Get a prioritization by ID"""
        return self.db.query(Prioritization).filter(Prioritization.id == prioritization_id).first()
    
    def get_project_prioritizations(
        self, 
        project_id: str, 
        filters: Optional[PrioritizationFilterParams] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Prioritization], int]:
        """Get prioritizations for a project with filtering and pagination"""
        
        query = self.db.query(Prioritization).filter(Prioritization.project_id == project_id)
        
        # Apply filters if provided
        if filters:
            if filters.item_type:
                query = query.filter(Prioritization.item_type == filters.item_type)
            
            if filters.priority_phase:
                query = query.filter(Prioritization.priority_phase == filters.priority_phase)
            
            if filters.min_score is not None:
                query = query.filter(Prioritization.score >= filters.min_score)
            
            if filters.max_score is not None:
                query = query.filter(Prioritization.score <= filters.max_score)
            
            if filters.assigned_by:
                query = query.filter(Prioritization.assigned_by == filters.assigned_by)
        
        # Get total count
        total = query.count()
        
        # Apply ordering
        if filters and filters.sort_by:
            if filters.sort_order == 'desc':
                query = query.order_by(desc(getattr(Prioritization, filters.sort_by)))
            else:
                query = query.order_by(asc(getattr(Prioritization, filters.sort_by)))
        else:
            # Default sort: phase, then position
            query = query.order_by(Prioritization.priority_phase, Prioritization.position)
        
        # Apply pagination
        prioritizations = query.offset(skip).limit(limit).all()
        
        return prioritizations, total
    
    def update_prioritization(
        self, 
        prioritization_id: str, 
        update_data: PrioritizationUpdate
    ) -> Optional[Prioritization]:
        """Update a prioritization"""
        
        prioritization = self.get_prioritization(prioritization_id)
        if not prioritization:
            return None
        
        # Handle phase changes (may require position updates)
        if update_data.priority_phase and update_data.priority_phase != prioritization.priority_phase:
            new_position = self._get_next_position(prioritization.project_id, update_data.priority_phase)
            prioritization.priority_phase = update_data.priority_phase
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
    
    def delete_prioritization(self, prioritization_id: str) -> bool:
        """Delete a prioritization"""
        
        prioritization = self.get_prioritization(prioritization_id)
        if not prioritization:
            return False
        
        self.db.delete(prioritization)
        self.db.commit()
        
        return True
    
    def bulk_update_prioritizations(
        self, 
        project_id: str, 
        bulk_update: BulkPrioritizationUpdate
    ) -> List[Prioritization]:
        """Bulk update prioritizations"""
        
        updated_prioritizations = []
        
        for update_item in bulk_update.updates:
            item_id = update_item.get('item_id')
            item_type = ItemType(update_item.get('item_type'))
            
            # Get or create prioritization
            prioritization = self.db.query(Prioritization).filter(
                and_(
                    Prioritization.project_id == project_id,
                    Prioritization.item_type == item_type,
                    Prioritization.item_id == item_id
                )
            ).first()
            
            if not prioritization:
                # Create new prioritization
                prioritization_data = PrioritizationCreate(
                    project_id=project_id,
                    item_type=item_type,
                    item_id=item_id,
                    priority_phase=PriorityPhase(update_item.get('priority_phase', PriorityPhase.UNASSIGNED.value)),
                    score=update_item.get('score'),
                    position=update_item.get('position', 0),
                    notes=update_item.get('notes'),
                    assigned_by=update_item.get('assigned_by')
                )
                prioritization = self.create_prioritization(prioritization_data)
            else:
                # Update existing prioritization
                if 'priority_phase' in update_item:
                    prioritization.priority_phase = PriorityPhase(update_item['priority_phase'])
                if 'score' in update_item:
                    prioritization.score = update_item['score']
                if 'position' in update_item:
                    prioritization.position = update_item['position']
                if 'notes' in update_item:
                    prioritization.notes = update_item['notes']
            
            updated_prioritizations.append(prioritization)
        
        self.db.commit()
        
        return updated_prioritizations
    
    def get_prioritization_board(self, project_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get prioritization board data organized by phases"""
        
        prioritizations = self.db.query(Prioritization).filter(
            Prioritization.project_id == project_id
        ).order_by(Prioritization.priority_phase, Prioritization.position).all()
        
        # Get all items that could be prioritized
        unassigned_items = self._get_unassigned_items(project_id)
        
        board = {
            'now': [],
            'next': [],
            'later': [],
            'unassigned': unassigned_items
        }
        
        # Organize prioritizations by phase
        for prioritization in prioritizations:
            item_data = self._get_item_data(prioritization)
            
            if prioritization.priority_phase == PriorityPhase.NOW:
                board['now'].append(item_data)
            elif prioritization.priority_phase == PriorityPhase.NEXT:
                board['next'].append(item_data)
            elif prioritization.priority_phase == PriorityPhase.LATER:
                board['later'].append(item_data)
            else:
                board['unassigned'].append(item_data)
        
        return board
    
    def get_prioritization_stats(self, project_id: str) -> Dict[str, Any]:
        """Get prioritization statistics for a project"""
        
        # Count total items by type
        object_count = self.db.query(Object).filter(Object.project_id == project_id).count()
        cta_count = self.db.query(CTA).filter(CTA.project_id == project_id).count()
        attribute_count = self.db.query(Attribute).filter(Attribute.project_id == project_id).count()
        relationship_count = self.db.query(Relationship).filter(
            or_(Relationship.source_project_id == project_id, Relationship.target_project_id == project_id)
        ).count()
        
        total_items = object_count + cta_count + attribute_count + relationship_count
        
        # Count prioritizations by phase
        prioritization_counts = self.db.query(
            Prioritization.priority_phase, 
            func.count(Prioritization.id)
        ).filter(
            Prioritization.project_id == project_id
        ).group_by(Prioritization.priority_phase).all()
        
        phase_counts = {phase.value: 0 for phase in PriorityPhase}
        for phase, count in prioritization_counts:
            phase_counts[phase.value] = count
        
        # Count by item type and phase
        by_item_type = {}
        for item_type in ItemType:
            type_counts = self.db.query(
                Prioritization.priority_phase,
                func.count(Prioritization.id)
            ).filter(
                and_(
                    Prioritization.project_id == project_id,
                    Prioritization.item_type == item_type
                )
            ).group_by(Prioritization.priority_phase).all()
            
            by_item_type[item_type.value] = {phase.value: 0 for phase in PriorityPhase}
            for phase, count in type_counts:
                by_item_type[item_type.value][phase.value] = count
        
        # Score statistics
        scored_prioritizations = self.db.query(Prioritization.score).filter(
            and_(
                Prioritization.project_id == project_id,
                Prioritization.score.isnot(None)
            )
        ).all()
        
        scored_items = len(scored_prioritizations)
        average_score = None
        if scored_items > 0:
            total_score = sum(p.score for p in scored_prioritizations)
            average_score = total_score / scored_items
        
        return {
            'total_items': total_items,
            'prioritized_items': sum(phase_counts.values()),
            'now_count': phase_counts['now'],
            'next_count': phase_counts['next'],
            'later_count': phase_counts['later'],
            'unassigned_count': total_items - sum(phase_counts.values()),
            'by_item_type': by_item_type,
            'average_score': average_score,
            'scored_items': scored_items
        }
    
    def create_snapshot(self, snapshot_data: PrioritizationSnapshotCreate) -> PrioritizationSnapshot:
        """Create a prioritization snapshot"""
        
        # Get current prioritization state
        prioritizations = self.db.query(Prioritization).filter(
            Prioritization.project_id == snapshot_data.project_id
        ).all()
        
        snapshot_state = []
        for p in prioritizations:
            snapshot_state.append({
                'item_type': p.item_type.value,
                'item_id': p.item_id,
                'priority_phase': p.priority_phase.value,
                'score': p.score,
                'position': p.position,
                'notes': p.notes,
                'assigned_by': p.assigned_by,
                'assigned_at': p.assigned_at.isoformat() if p.assigned_at else None
            })
        
        snapshot = PrioritizationSnapshot(
            project_id=snapshot_data.project_id,
            snapshot_name=snapshot_data.snapshot_name,
            description=snapshot_data.description,
            created_by=snapshot_data.created_by,
            snapshot_data=json.dumps(snapshot_state)
        )
        
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        
        return snapshot
    
    def _verify_item_exists(self, item_type: ItemType, item_id: str) -> bool:
        """Verify that the item exists in the database"""
        
        if item_type == ItemType.OBJECT:
            item = self.db.query(Object).filter(Object.id == item_id).first()
        elif item_type == ItemType.CTA:
            item = self.db.query(CTA).filter(CTA.id == item_id).first()
        elif item_type == ItemType.ATTRIBUTE:
            item = self.db.query(Attribute).filter(Attribute.id == item_id).first()
        elif item_type == ItemType.RELATIONSHIP:
            item = self.db.query(Relationship).filter(Relationship.id == item_id).first()
        else:
            return False
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{item_type.value.title()} with ID {item_id} not found"
            )
        
        return True
    
    def _get_next_position(self, project_id: str, priority_phase: PriorityPhase) -> int:
        """Get the next position for an item in a priority phase"""
        
        max_position = self.db.query(func.max(Prioritization.position)).filter(
            and_(
                Prioritization.project_id == project_id,
                Prioritization.priority_phase == priority_phase
            )
        ).scalar()
        
        return (max_position or 0) + 1
    
    def _get_unassigned_items(self, project_id: str) -> List[Dict[str, Any]]:
        """Get items that don't have prioritization assignments"""
        
        # Get all items from the project
        objects = self.db.query(Object).filter(Object.project_id == project_id).all()
        ctas = self.db.query(CTA).filter(CTA.project_id == project_id).all()
        attributes = self.db.query(Attribute).filter(Attribute.project_id == project_id).all()
        relationships = self.db.query(Relationship).filter(
            or_(Relationship.source_project_id == project_id, Relationship.target_project_id == project_id)
        ).all()
        
        # Get prioritized item IDs
        prioritized_items = self.db.query(
            Prioritization.item_type, 
            Prioritization.item_id
        ).filter(Prioritization.project_id == project_id).all()
        
        prioritized_set = {(p.item_type, p.item_id) for p in prioritized_items}
        
        unassigned = []
        
        # Add unassigned objects
        for obj in objects:
            if (ItemType.OBJECT, obj.id) not in prioritized_set:
                unassigned.append({
                    'item_type': ItemType.OBJECT.value,
                    'item_id': obj.id,
                    'item_name': obj.name,
                    'item_description': obj.definition,
                    'priority_phase': PriorityPhase.UNASSIGNED.value
                })
        
        # Add unassigned CTAs
        for cta in ctas:
            if (ItemType.CTA, cta.id) not in prioritized_set:
                unassigned.append({
                    'item_type': ItemType.CTA.value,
                    'item_id': cta.id,
                    'item_name': f"{cta.object_name}.{cta.name}",
                    'item_description': cta.trigger or cta.business_rules,
                    'priority_phase': PriorityPhase.UNASSIGNED.value
                })
        
        # Add unassigned attributes
        for attr in attributes:
            if (ItemType.ATTRIBUTE, attr.id) not in prioritized_set:
                unassigned.append({
                    'item_type': ItemType.ATTRIBUTE.value,
                    'item_id': attr.id,
                    'item_name': attr.name,
                    'item_description': attr.description,
                    'priority_phase': PriorityPhase.UNASSIGNED.value
                })
        
        # Add unassigned relationships
        for rel in relationships:
            if (ItemType.RELATIONSHIP, rel.id) not in prioritized_set:
                unassigned.append({
                    'item_type': ItemType.RELATIONSHIP.value,
                    'item_id': rel.id,
                    'item_name': f"{rel.source_object} → {rel.target_object}",
                    'item_description': rel.description,
                    'priority_phase': PriorityPhase.UNASSIGNED.value
                })
        
        return unassigned
    
    def _get_item_data(self, prioritization: Prioritization) -> Dict[str, Any]:
        """Get enriched item data for a prioritization"""
        
        base_data = {
            'id': prioritization.id,
            'item_type': prioritization.item_type.value,
            'item_id': prioritization.item_id,
            'priority_phase': prioritization.priority_phase.value,
            'score': prioritization.score,
            'position': prioritization.position,
            'notes': prioritization.notes,
            'assigned_by': prioritization.assigned_by,
            'assigned_at': prioritization.assigned_at,
            'updated_at': prioritization.updated_at
        }
        
        # Get item details
        if prioritization.item_type == ItemType.OBJECT:
            item = self.db.query(Object).filter(Object.id == prioritization.item_id).first()
            if item:
                base_data.update({
                    'item_name': item.name,
                    'item_description': item.definition
                })
        elif prioritization.item_type == ItemType.CTA:
            item = self.db.query(CTA).filter(CTA.id == prioritization.item_id).first()
            if item:
                base_data.update({
                    'item_name': f"{item.object_name}.{item.name}",
                    'item_description': item.trigger or item.business_rules
                })
        elif prioritization.item_type == ItemType.ATTRIBUTE:
            item = self.db.query(Attribute).filter(Attribute.id == prioritization.item_id).first()
            if item:
                base_data.update({
                    'item_name': item.name,
                    'item_description': item.description
                })
        elif prioritization.item_type == ItemType.RELATIONSHIP:
            item = self.db.query(Relationship).filter(Relationship.id == prioritization.item_id).first()
            if item:
                base_data.update({
                    'item_name': f"{item.source_object} → {item.target_object}",
                    'item_description': item.description
                })
        
        return base_data
