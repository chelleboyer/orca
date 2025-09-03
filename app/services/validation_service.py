"""
Service layer for project validation and completeness analysis.
Builds on CDLL completion scoring to provide project-wide validation.
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from datetime import datetime
import uuid

from app.models.object import Object
from app.models.attribute import Attribute, ObjectAttribute
from app.models.cta import CTA, CRUDType
from app.models.relationship import Relationship
from app.models.prioritization import Prioritization, PriorityPhase, ItemType
from app.models.role import Role
from app.services.cdll_preview_service import CDLLPreviewService


class ValidationService:
    """Service for project-wide validation and completeness analysis."""

    def __init__(self, db: Session):
        self.db = db
        self.cdll_service = CDLLPreviewService(db)

    def get_project_validation_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Get comprehensive validation summary for entire project.
        
        Args:
            project_id: UUID of the project to validate
            
        Returns:
            Complete validation summary with scores and recommendations
        """
        # Get all objects in project
        objects = self.db.query(Object).filter(
            Object.project_id == project_id
        ).all()

        if not objects:
            return self._empty_project_validation()

        # Calculate individual object scores
        object_validations = []
        total_score = 0
        
        for obj in objects:
            obj_validation = self._validate_single_object(obj)
            object_validations.append(obj_validation)
            total_score += obj_validation["completion_score"]

        # Calculate project-wide metrics
        overall_completion = total_score / len(objects) if objects else 0
        
        # Analyze project dimensions
        dimension_scores = self._analyze_project_dimensions(project_id)
        
        # Generate project-level recommendations
        recommendations = self._generate_project_recommendations(
            objects, object_validations, dimension_scores
        )
        
        # Determine export readiness
        export_readiness = self._assess_export_readiness(
            overall_completion, dimension_scores, object_validations
        )

        return {
            "project_id": project_id,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "overall_completion": round(overall_completion, 1),
            "export_ready": export_readiness["ready"],
            "export_readiness_details": export_readiness,
            "dimension_scores": dimension_scores,
            "object_count": len(objects),
            "object_validations": object_validations,
            "recommendations": recommendations,
            "validation_rules": self._get_validation_rules_summary()
        }

    def get_object_validation_details(self, project_id: str, object_id: str) -> Dict[str, Any]:
        """
        Get detailed validation information for a specific object.
        
        Args:
            project_id: UUID of the project
            object_id: UUID of the object to validate
            
        Returns:
            Detailed validation data for the object
        """
        obj = self.db.query(Object).filter(
            and_(
                Object.id == object_id,
                Object.project_id == project_id
            )
        ).first()

        if not obj:
            raise ValueError(f"Object {object_id} not found in project {project_id}")

        return self._validate_single_object(obj, detailed=True)

    def get_validation_gaps(self, project_id: str, priority_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Get gaps and missing elements across the project.
        
        Args:
            project_id: UUID of the project
            priority_filter: Filter by priority phase (now/next/later)
            
        Returns:
            Comprehensive gap analysis
        """
        objects = self._get_filtered_objects(project_id, priority_filter)
        
        gaps = {
            "missing_definitions": [],
            "insufficient_attributes": [],
            "missing_ctas": [],
            "isolated_objects": [],
            "incomplete_relationships": [],
            "priority_issues": []
        }

        for obj in objects:
            obj_data = self._prepare_object_data(obj)
            
            # Check for missing definitions
            if not obj_data["definition"] or len(obj_data["definition"].strip()) < 10:
                gaps["missing_definitions"].append({
                    "object_id": str(obj.id),
                    "object_name": obj.name,
                    "issue": "Definition missing or too short",
                    "recommendation": "Add clear description of object purpose"
                })
            
            # Check for insufficient core attributes
            if len(obj_data["core_attributes"]) < 2:
                gaps["insufficient_attributes"].append({
                    "object_id": str(obj.id),
                    "object_name": obj.name,
                    "core_count": len(obj_data["core_attributes"]),
                    "recommendation": "Mark 3-5 key attributes as core"
                })
            
            # Check for missing CTAs
            if len(obj_data["primary_ctas"]) == 0:
                gaps["missing_ctas"].append({
                    "object_id": str(obj.id),
                    "object_name": obj.name,
                    "issue": "No primary CTAs defined",
                    "recommendation": "Define key user actions for this object"
                })
            
            # Check for relationship isolation
            if obj_data["relationship_count"] == 0:
                gaps["isolated_objects"].append({
                    "object_id": str(obj.id),
                    "object_name": obj.name,
                    "issue": "Object has no relationships",
                    "recommendation": "Define how this object relates to others"
                })

        return {
            "project_id": project_id,
            "priority_filter": priority_filter,
            "gap_summary": {
                "missing_definitions": len(gaps["missing_definitions"]),
                "insufficient_attributes": len(gaps["insufficient_attributes"]),
                "missing_ctas": len(gaps["missing_ctas"]),
                "isolated_objects": len(gaps["isolated_objects"])
            },
            "gaps": gaps,
            "total_gaps": sum(len(gap_list) for gap_list in gaps.values())
        }

    def _validate_single_object(self, obj: Object, detailed: bool = False) -> Dict[str, Any]:
        """Validate a single object using CDLL completion patterns."""
        
        obj_data = self._prepare_object_data(obj)
        
        # Use existing CDLL completion scoring
        completion_data = self.cdll_service._calculate_completion_score(obj_data)
        warnings = self.cdll_service._generate_warnings(obj_data)
        
        validation_result = {
            "object_id": str(obj.id),
            "object_name": obj.name,
            "completion_score": completion_data["total_score"],
            "completion_grade": self.cdll_service._get_completion_grade(completion_data["total_score"]),
            "warnings_count": len(warnings),
            "export_ready": completion_data["total_score"] >= 60  # Minimum for export
        }
        
        if detailed:
            validation_result.update({
                "completion_breakdown": completion_data,
                "warnings": warnings,
                "object_data": obj_data,
                "recommendations": self._generate_object_recommendations(obj_data, warnings)
            })
            
        return validation_result

    def _prepare_object_data(self, obj: Object) -> Dict[str, Any]:
        """Prepare object data in format expected by CDLL service."""
        
        # Get attributes
        attributes = self.db.query(ObjectAttribute).filter(
            ObjectAttribute.object_id == obj.id
        ).all()
        
        core_attributes = [attr for attr in attributes if getattr(attr, 'is_core', False)]
        
        # Get CTAs
        ctas = self.db.query(CTA).filter(
            CTA.object_id == obj.id
        ).all()
        
        primary_ctas = [cta for cta in ctas if getattr(cta, 'is_primary', False)]
        
        # Get relationships
        relationships = self.db.query(Relationship).filter(
            (Relationship.source_object_id == obj.id) |
            (Relationship.target_object_id == obj.id)
        ).all()
        
        return {
            "id": str(obj.id),
            "name": obj.name,
            "definition": obj.definition or "",
            "core_attributes": [{"name": attr.attribute.name if attr.attribute else "Unknown"} 
                             for attr in core_attributes],
            "all_attributes": [{"name": attr.attribute.name if attr.attribute else "Unknown"} 
                             for attr in attributes],
            "primary_ctas": [{"name": cta.name, "crud_type": cta.crud_type.value} 
                           for cta in primary_ctas],
            "all_ctas": [{"name": cta.name, "crud_type": cta.crud_type.value} 
                        for cta in ctas],
            "relationship_count": len(relationships)
        }

    def _analyze_project_dimensions(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        """Analyze completion across all OOUX dimensions."""
        
        # Objects dimension
        objects_count = self.db.query(Object).filter(
            Object.project_id == project_id
        ).count()
        
        objects_with_definition = self.db.query(Object).filter(
            and_(
                Object.project_id == project_id,
                Object.definition.isnot(None),
                func.length(Object.definition) > 10
            )
        ).count()
        
        # Attributes dimension
        total_attributes = self.db.query(ObjectAttribute).join(Object).filter(
            Object.project_id == project_id
        ).count()
        
        core_attributes = self.db.query(ObjectAttribute).join(Object).join(Attribute).filter(
            and_(
                Object.project_id == project_id,
                Attribute.is_core == True
            )
        ).count()
        
        # CTAs dimension
        total_ctas = self.db.query(CTA).filter(
            CTA.project_id == project_id
        ).count()
        
        primary_ctas = self.db.query(CTA).filter(
            and_(
                CTA.project_id == project_id,
                CTA.is_primary == True
            )
        ).count()
        
        # Relationships dimension
        total_relationships = self.db.query(Relationship).filter(
            Relationship.project_id == project_id
        ).count()
        
        # Prioritization dimension
        prioritized_items = self.db.query(Prioritization).filter(
            Prioritization.project_id == project_id
        ).count()
        
        return {
            "objects": {
                "total": objects_count,
                "with_definition": objects_with_definition,
                "completion_percentage": (objects_with_definition / objects_count * 100) if objects_count > 0 else 0,
                "status": "complete" if objects_with_definition == objects_count else "incomplete"
            },
            "attributes": {
                "total": total_attributes,
                "core": core_attributes,
                "completion_percentage": (core_attributes / max(objects_count * 3, 1) * 100),  # Target 3 core per object
                "status": "complete" if core_attributes >= objects_count * 2 else "incomplete"
            },
            "ctas": {
                "total": total_ctas,
                "primary": primary_ctas,
                "completion_percentage": (primary_ctas / max(objects_count, 1) * 100),  # Target 1+ primary per object
                "status": "complete" if primary_ctas >= objects_count else "incomplete"
            },
            "relationships": {
                "total": total_relationships,
                "potential": objects_count * (objects_count - 1) if objects_count > 1 else 0,
                "completion_percentage": (total_relationships / max(objects_count * 2, 1) * 100),  # Target 2 per object
                "status": "complete" if total_relationships >= objects_count else "incomplete"
            },
            "prioritization": {
                "total": prioritized_items,
                "completion_percentage": (prioritized_items / max(objects_count + total_ctas + total_attributes, 1) * 100),
                "status": "complete" if prioritized_items > 0 else "incomplete"
            }
        }

    def _assess_export_readiness(self, overall_completion: float, dimension_scores: Dict, 
                                object_validations: List[Dict]) -> Dict[str, Any]:
        """Assess if project is ready for development handoff."""
        
        # Calculate readiness criteria
        min_completion = 60  # Minimum overall completion
        min_objects_ready = 0.8  # 80% of objects must be export-ready
        
        objects_ready = sum(1 for obj in object_validations if obj["export_ready"])
        objects_ready_percentage = (objects_ready / len(object_validations)) if object_validations else 0
        
        # Check critical dimensions
        critical_dimensions = ["objects", "attributes", "ctas"]
        critical_complete = all(
            dimension_scores[dim]["completion_percentage"] >= 50 
            for dim in critical_dimensions
        )
        
        ready = (
            overall_completion >= min_completion and
            objects_ready_percentage >= min_objects_ready and
            critical_complete
        )
        
        return {
            "ready": ready,
            "overall_completion": overall_completion,
            "min_completion_threshold": min_completion,
            "objects_ready": objects_ready,
            "objects_ready_percentage": round(objects_ready_percentage * 100, 1),
            "min_objects_ready_threshold": min_objects_ready * 100,
            "critical_dimensions_complete": critical_complete,
            "blocking_issues": self._identify_blocking_issues(dimension_scores, object_validations)
        }

    def _generate_project_recommendations(self, objects: List[Object], 
                                        object_validations: List[Dict],
                                        dimension_scores: Dict) -> List[Dict[str, str]]:
        """Generate actionable recommendations for project improvement."""
        
        recommendations = []
        
        # Object-level recommendations
        low_score_objects = [obj for obj in object_validations if obj["completion_score"] < 40]
        if len(low_score_objects) > len(objects) * 0.3:  # More than 30% low scoring
            recommendations.append({
                "type": "objects",
                "priority": "high",
                "title": "Improve Object Definitions",
                "description": f"{len(low_score_objects)} objects need better definitions and core attributes",
                "action": "Focus on completing definitions and marking core attributes"
            })
        
        # Dimension-specific recommendations
        for dim_name, dim_data in dimension_scores.items():
            if dim_data["completion_percentage"] < 50:
                recommendations.append({
                    "type": dim_name,
                    "priority": "medium",
                    "title": f"Improve {dim_name.title()} Coverage",
                    "description": f"{dim_name.title()} dimension is only {dim_data['completion_percentage']:.1f}% complete",
                    "action": f"Add more {dim_name} to reach minimum viable coverage"
                })
        
        return recommendations

    def _identify_blocking_issues(self, dimension_scores: Dict, object_validations: List[Dict]) -> List[str]:
        """Identify issues that block export readiness."""
        
        blocking_issues = []
        
        # Check for critical dimension failures
        if dimension_scores["objects"]["completion_percentage"] < 30:
            blocking_issues.append("Too many objects lack proper definitions")
            
        if dimension_scores["ctas"]["completion_percentage"] < 30:
            blocking_issues.append("Insufficient primary CTAs defined")
            
        # Check for widespread object failures
        failed_objects = sum(1 for obj in object_validations if obj["completion_score"] < 30)
        if failed_objects > len(object_validations) * 0.5:
            blocking_issues.append("More than 50% of objects are severely incomplete")
            
        return blocking_issues

    def _generate_object_recommendations(self, obj_data: Dict, warnings: List[Dict]) -> List[Dict[str, str]]:
        """Generate specific recommendations for object improvement."""
        
        recommendations = []
        
        for warning in warnings:
            recommendations.append({
                "type": warning["type"],
                "priority": "high" if warning["type"] in ["missing_definition", "no_primary_ctas"] else "medium",
                "title": warning["message"],
                "action": warning["suggestion"]
            })
            
        return recommendations

    def _get_filtered_objects(self, project_id: str, priority_filter: Optional[str]) -> List[Object]:
        """Get objects filtered by priority phase if specified."""
        
        query = self.db.query(Object).filter(Object.project_id == project_id)
        
        if priority_filter:
            # Join with prioritization to filter by phase
            try:
                priority_phase = PriorityPhase(priority_filter.lower())
                query = query.join(Prioritization, and_(
                    Prioritization.item_id == Object.id,
                    Prioritization.item_type == ItemType.OBJECT.value,
                    Prioritization.priority_phase == priority_phase.value
                ))
            except ValueError:
                # Invalid priority filter, return all objects
                pass
            
        return query.all()

    def _empty_project_validation(self) -> Dict[str, Any]:
        """Return validation result for empty project."""
        
        return {
            "project_id": "empty",
            "validation_timestamp": datetime.utcnow().isoformat(),
            "overall_completion": 0,
            "export_ready": False,
            "export_readiness_details": {
                "ready": False,
                "overall_completion": 0,
                "min_completion_threshold": 60,
                "objects_ready": 0,
                "objects_ready_percentage": 0,
                "min_objects_ready_threshold": 80,
                "critical_dimensions_complete": False,
                "blocking_issues": ["No objects defined in project"]
            },
            "dimension_scores": {},
            "object_count": 0,
            "object_validations": [],
            "recommendations": [{
                "type": "project",
                "priority": "high",
                "title": "Add Objects to Project",
                "description": "Project has no objects defined",
                "action": "Start by adding your first domain object"
            }],
            "validation_rules": self._get_validation_rules_summary()
        }

    def _get_validation_rules_summary(self) -> Dict[str, Any]:
        """Get summary of current validation rules and thresholds."""
        
        return {
            "completion_thresholds": {
                "definition_minimum": 10,
                "core_attributes_minimum": 2,
                "primary_ctas_minimum": 1,
                "export_readiness_minimum": 60
            },
            "scoring_weights": {
                "definition": 20,
                "core_attributes": 30,
                "primary_ctas": 25,
                "crud_coverage": 25
            },
            "configurable": False  # Future enhancement
        }
