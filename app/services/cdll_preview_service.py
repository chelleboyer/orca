"""
CDLL Preview Generation Service

Generates Cards, Details, Lists, and Landings previews for objects
using core attributes and primary CTAs to build realistic interfaces.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from jinja2 import Environment, BaseLoader
import json

from app.models.object import Object
from app.models.attribute import Attribute, ObjectAttribute
from app.models.cta import CTA, CRUDType
from app.models.prioritization import Prioritization, PriorityPhase, ItemType
from app.models.project import Project


class CDLLPreviewService:
    """Service for generating CDLL (Cards/Details/Lists/Landings) previews."""

    def __init__(self, db: Session):
        self.db = db

    def generate_object_previews(
        self, project_id: str, object_id: str
    ) -> Dict[str, Any]:
        """Generate all CDLL previews for a specific object."""
        
        # Get object with all related data
        obj = self._get_object_with_data(project_id, object_id)
        if not obj:
            raise ValueError(f"Object {object_id} not found in project {project_id}")

        # Get prioritization status
        prioritization = self._get_object_prioritization(project_id, object_id)
        
        # Generate each preview type
        previews = {
            "object_id": object_id,
            "object_name": obj["name"],
            "priority_phase": prioritization.priority_phase.value if prioritization else "unassigned",
            "card": self._generate_card_preview(obj),
            "detail": self._generate_detail_preview(obj),
            "list": self._generate_list_preview(obj),
            "landing": self._generate_landing_preview(obj),
            "warnings": self._generate_warnings(obj),
            "completion_score": self._calculate_completion_score(obj)
        }

        return previews

    def generate_project_previews(
        self, project_id: str, priority_filter: Optional[PriorityPhase] = None
    ) -> List[Dict[str, Any]]:
        """Generate CDLL previews for all objects in a project."""
        
        # Get all objects in project
        query = self.db.query(Object).filter(Object.project_id == project_id)
        
        # Filter by priority if specified
        if priority_filter:
            prioritized_object_ids = self.db.query(Prioritization.item_id).filter(
                and_(
                    Prioritization.project_id == project_id,
                    Prioritization.item_type == ItemType.OBJECT,
                    Prioritization.priority_phase == priority_filter
                )
            )
            
            query = query.filter(Object.id.in_(prioritized_object_ids))

        objects = query.order_by(Object.name).all()

        previews = []
        for obj in objects:
            try:
                preview = self.generate_object_previews(project_id, str(obj.id))
                previews.append(preview)
            except Exception as e:
                # Log error but continue with other objects
                previews.append({
                    "object_id": str(obj.id),
                    "object_name": obj.name,
                    "error": str(e),
                    "priority_phase": "unassigned"
                })

        return previews

    def export_previews_html(
        self, project_id: str, preview_data: List[Dict[str, Any]]
    ) -> str:
        """Export CDLL previews as HTML with embedded CSS."""
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        html_template = self._get_export_html_template()
        
        return html_template.format(
            project_name=project.title,
            project_description=project.description or "No description provided",
            preview_data=json.dumps(preview_data, indent=2),
            previews_html=self._render_previews_html(preview_data),
            css_styles=self._get_preview_css_styles()
        )

    def _get_object_with_data(self, project_id: str, object_id: str) -> Optional[Dict[str, Any]]:
        """Get object with all related attributes and CTAs."""
        
        obj = self.db.query(Object).filter(
            and_(Object.id == object_id, Object.project_id == project_id)
        ).first()
        
        if not obj:
            return None

        # Get core attributes
        core_attributes = self.db.query(ObjectAttribute, Attribute).join(
            Attribute
        ).filter(
            and_(
                ObjectAttribute.object_id == object_id,
                Attribute.is_core == True,  # type: ignore
                Attribute.is_active == True  # type: ignore
            )
        ).order_by(Attribute.name).all()

        # Get all attributes
        all_attributes = self.db.query(ObjectAttribute, Attribute).join(
            Attribute
        ).filter(
            and_(
                ObjectAttribute.object_id == object_id,
                Attribute.is_active == True  # type: ignore
            )
        ).order_by(Attribute.name).all()

        # Get primary CTAs
        primary_ctas = self.db.query(CTA).filter(
            and_(
                CTA.object_id == object_id,
                CTA.is_primary == True  # type: ignore
            )
        ).order_by(CTA.display_order, CTA.description).all()

        # Get all CTAs
        all_ctas = self.db.query(CTA).filter(
            CTA.object_id == object_id
        ).order_by(CTA.display_order, CTA.description).all()

        return {
            "id": str(obj.id),
            "name": obj.name,
            "definition": obj.definition,
            "core_attributes": [
                {
                    "name": attr.name,
                    "data_type": attr.data_type.value,
                    "value": obj_attr.value,
                    "required": False  # Default to False since ObjectAttribute doesn't have is_required
                }
                for obj_attr, attr in core_attributes
            ],
            "all_attributes": [
                {
                    "name": attr.name,
                    "data_type": attr.data_type.value,
                    "value": obj_attr.value,
                    "required": False,  # Default to False since ObjectAttribute doesn't have is_required
                    "is_core": attr.is_core
                }
                for obj_attr, attr in all_attributes
            ],
            "primary_ctas": [
                {
                    "description": cta.description,
                    "crud_type": cta.crud_type,
                    "business_value": cta.business_value
                }
                for cta in primary_ctas
            ],
            "all_ctas": [
                {
                    "description": cta.description,
                    "crud_type": cta.crud_type,
                    "business_value": cta.business_value,
                    "is_primary": cta.is_primary
                }
                for cta in all_ctas
            ]
        }

    def _get_object_prioritization(
        self, project_id: str, object_id: str
    ) -> Optional[Prioritization]:
        """Get prioritization for an object."""
        
        return self.db.query(Prioritization).filter(
            and_(
                Prioritization.project_id == project_id,
                Prioritization.item_type == ItemType.OBJECT,
                Prioritization.item_id == object_id
            )
        ).first()

    def _generate_card_preview(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Card preview - compact view with key information."""
        
        # Use first 3 core attributes for card
        display_attributes = obj["core_attributes"][:3]
        
        # Use first primary CTA for action
        primary_action = obj["primary_ctas"][0] if obj["primary_ctas"] else None
        
        return {
            "type": "card",
            "title": obj["name"],
            "subtitle": obj["definition"][:100] + "..." if obj["definition"] and len(obj["definition"]) > 100 else obj["definition"],
            "attributes": display_attributes,
            "primary_action": primary_action,
            "html": self._render_card_html(obj, display_attributes, primary_action)
        }

    def _generate_detail_preview(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Detail preview - full object view with all information."""
        
        return {
            "type": "detail",
            "title": obj["name"],
            "definition": obj["definition"],
            "attributes": obj["all_attributes"],
            "actions": obj["all_ctas"],
            "html": self._render_detail_html(obj)
        }

    def _generate_list_preview(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Generate List preview - table row view for browsing multiple objects."""
        
        # Use core attributes for list columns
        list_columns = obj["core_attributes"][:5]  # Max 5 columns for readability
        
        return {
            "type": "list",
            "columns": ["Name"] + [attr["name"] for attr in list_columns],
            "values": [obj["name"]] + [attr["value"] or "—" for attr in list_columns],
            "html": self._render_list_html(obj, list_columns)
        }

    def _generate_landing_preview(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Landing preview - overview page with navigation and key actions."""
        
        # Group CTAs by CRUD type for organized display
        cta_groups = {}
        for cta in obj["all_ctas"]:
            crud_type = cta["crud_type"]
            if crud_type not in cta_groups:
                cta_groups[crud_type] = []
            cta_groups[crud_type].append(cta)

        return {
            "type": "landing",
            "title": obj["name"],
            "definition": obj["definition"],
            "core_attributes": obj["core_attributes"],
            "cta_groups": cta_groups,
            "html": self._render_landing_html(obj, cta_groups)
        }

    def _generate_warnings(self, obj: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate warnings for missing critical information."""
        
        warnings = []

        # Check for missing definition
        if not obj["definition"] or len(obj["definition"].strip()) < 10:
            warnings.append({
                "type": "missing_definition",
                "message": "Object definition is missing or too short. Add a clear description of what this object represents.",
                "suggestion": "Add a definition explaining the purpose and key characteristics of this object."
            })

        # Check for missing core attributes
        if len(obj["core_attributes"]) < 2:
            warnings.append({
                "type": "insufficient_core_attributes",
                "message": f"Only {len(obj['core_attributes'])} core attributes defined. Objects typically need 3-5 core attributes for meaningful UI generation.",
                "suggestion": "Mark 3-5 key attributes as 'core' to improve preview quality."
            })

        # Check for missing primary CTAs
        if len(obj["primary_ctas"]) == 0:
            warnings.append({
                "type": "no_primary_ctas",
                "message": "No primary CTAs defined. Primary actions are essential for user interface design.",
                "suggestion": "Mark the most common user actions as 'primary' CTAs."
            })

        # Check for missing READ CTA
        read_ctas = [cta for cta in obj["all_ctas"] if cta["crud_type"] == CRUDType.READ.value]
        if not read_ctas:
            warnings.append({
                "type": "no_read_cta",
                "message": "No READ CTA defined. Users need a way to view object details.",
                "suggestion": "Add a READ CTA describing how users can view this object."
            })

        return warnings

    def _calculate_completion_score(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate completion score for CDLL generation readiness."""
        
        score = 0
        max_score = 100
        details = {}

        # Definition completeness (20 points)
        if obj["definition"] and len(obj["definition"].strip()) >= 20:
            score += 20
            details["definition"] = {"score": 20, "status": "complete"}
        elif obj["definition"] and len(obj["definition"].strip()) >= 10:
            score += 10
            details["definition"] = {"score": 10, "status": "partial"}
        else:
            details["definition"] = {"score": 0, "status": "missing"}

        # Core attributes (30 points)
        core_count = len(obj["core_attributes"])
        if core_count >= 4:
            score += 30
            details["core_attributes"] = {"score": 30, "status": "excellent"}
        elif core_count >= 2:
            score += 20
            details["core_attributes"] = {"score": 20, "status": "good"}
        elif core_count >= 1:
            score += 10
            details["core_attributes"] = {"score": 10, "status": "minimal"}
        else:
            details["core_attributes"] = {"score": 0, "status": "missing"}

        # Primary CTAs (25 points)
        primary_count = len(obj["primary_ctas"])
        if primary_count >= 3:
            score += 25
            details["primary_ctas"] = {"score": 25, "status": "excellent"}
        elif primary_count >= 2:
            score += 20
            details["primary_ctas"] = {"score": 20, "status": "good"}
        elif primary_count >= 1:
            score += 15
            details["primary_ctas"] = {"score": 15, "status": "minimal"}
        else:
            details["primary_ctas"] = {"score": 0, "status": "missing"}

        # CRUD coverage (25 points)
        crud_types = set(cta["crud_type"] for cta in obj["all_ctas"])
        crud_score = len(crud_types) * 6  # Max 4 types * 6 = 24, plus 1 for having any
        if crud_types:
            crud_score += 1
        score += min(crud_score, 25)
        details["crud_coverage"] = {"score": min(crud_score, 25), "types": list(crud_types)}

        return {
            "total_score": score,
            "max_score": max_score,
            "percentage": round((score / max_score) * 100),
            "grade": self._get_completion_grade(score),
            "details": details
        }

    def _get_completion_grade(self, score: int) -> str:
        """Get letter grade based on completion score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _render_card_html(
        self, obj: Dict[str, Any], attributes: List[Dict[str, Any]], action: Optional[Dict[str, Any]]
    ) -> str:
        """Render HTML for card preview."""
        
        attributes_html = ""
        for attr in attributes:
            attributes_html += f"""
                <div class="card-attribute">
                    <span class="attr-label">{attr['name']}:</span>
                    <span class="attr-value">{attr['value'] or '—'}</span>
                </div>
            """

        action_html = ""
        if action:
            action_html = f"""
                <div class="card-action">
                    <button class="btn btn-primary">{action['description']}</button>
                </div>
            """

        return f"""
            <div class="object-card">
                <div class="card-header">
                    <h3 class="card-title">{obj['name']}</h3>
                    <p class="card-subtitle">{obj['definition'][:100] + '...' if obj['definition'] and len(obj['definition']) > 100 else obj['definition'] or ''}</p>
                </div>
                <div class="card-body">
                    <div class="card-attributes">
                        {attributes_html}
                    </div>
                    {action_html}
                </div>
            </div>
        """

    def _render_detail_html(self, obj: Dict[str, Any]) -> str:
        """Render HTML for detail preview."""
        
        attributes_html = ""
        for attr in obj["all_attributes"]:
            core_badge = '<span class="core-badge">Core</span>' if attr["is_core"] else ""
            required_badge = '<span class="required-badge">Required</span>' if attr["required"] else ""
            
            attributes_html += f"""
                <div class="detail-attribute">
                    <div class="attr-header">
                        <span class="attr-name">{attr['name']}</span>
                        <span class="attr-type">({attr['data_type']})</span>
                        {core_badge}
                        {required_badge}
                    </div>
                    <div class="attr-value">{attr['value'] or '—'}</div>
                </div>
            """

        actions_html = ""
        for cta in obj["all_ctas"]:
            primary_class = "primary" if cta["is_primary"] else ""
            actions_html += f"""
                <div class="detail-action {primary_class}">
                    <span class="crud-badge crud-{cta['crud_type'].lower()}">{cta['crud_type']}</span>
                    <span class="action-description">{cta['description']}</span>
                </div>
            """

        return f"""
            <div class="object-detail">
                <div class="detail-header">
                    <h2 class="detail-title">{obj['name']}</h2>
                    <p class="detail-definition">{obj['definition'] or 'No definition provided'}</p>
                </div>
                
                <div class="detail-section">
                    <h3>Attributes</h3>
                    <div class="detail-attributes">
                        {attributes_html}
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>Available Actions</h3>
                    <div class="detail-actions">
                        {actions_html}
                    </div>
                </div>
            </div>
        """

    def _render_list_html(self, obj: Dict[str, Any], columns: List[Dict[str, Any]]) -> str:
        """Render HTML for list preview."""
        
        headers_html = "<th>Name</th>"
        for col in columns:
            headers_html += f"<th>{col['name']}</th>"

        values_html = f"<td><strong>{obj['name']}</strong></td>"
        for col in columns:
            values_html += f"<td>{col['value'] or '—'}</td>"

        return f"""
            <div class="object-list">
                <table class="list-table">
                    <thead>
                        <tr>{headers_html}</tr>
                    </thead>
                    <tbody>
                        <tr>{values_html}</tr>
                    </tbody>
                </table>
            </div>
        """

    def _render_landing_html(self, obj: Dict[str, Any], cta_groups: Dict[str, List[Dict[str, Any]]]) -> str:
        """Render HTML for landing preview."""
        
        # Core attributes summary
        core_attrs_html = ""
        for attr in obj["core_attributes"]:
            core_attrs_html += f"""
                <div class="landing-attribute">
                    <span class="attr-label">{attr['name']}:</span>
                    <span class="attr-value">{attr['value'] or '—'}</span>
                </div>
            """

        # Action groups
        action_groups_html = ""
        for crud_type, ctas in cta_groups.items():
            if ctas:  # Only show groups with CTAs
                ctas_html = ""
                for cta in ctas:
                    primary_class = "primary" if cta["is_primary"] else ""
                    ctas_html += f"""
                        <button class="landing-action {primary_class}">
                            {cta['description']}
                        </button>
                    """
                
                action_groups_html += f"""
                    <div class="action-group">
                        <h4 class="group-title">{crud_type.title()} Actions</h4>
                        <div class="group-actions">
                            {ctas_html}
                        </div>
                    </div>
                """

        return f"""
            <div class="object-landing">
                <div class="landing-header">
                    <h1 class="landing-title">{obj['name']}</h1>
                    <p class="landing-description">{obj['definition'] or 'No description provided'}</p>
                </div>
                
                <div class="landing-summary">
                    <h3>Key Information</h3>
                    <div class="landing-attributes">
                        {core_attrs_html}
                    </div>
                </div>
                
                <div class="landing-actions">
                    <h3>What You Can Do</h3>
                    <div class="action-groups">
                        {action_groups_html}
                    </div>
                </div>
            </div>
        """

    def _render_previews_html(self, preview_data: List[Dict[str, Any]]) -> str:
        """Render HTML for all previews in export."""
        
        html = ""
        
        for preview in preview_data:
            if "error" in preview:
                html += f"""
                    <div class="preview-error">
                        <h2>{preview['object_name']} - Error</h2>
                        <p class="error-message">{preview['error']}</p>
                    </div>
                """
                continue

            warnings_html = ""
            if preview["warnings"]:
                warnings_list = ""
                for warning in preview["warnings"]:
                    warnings_list += f"<li>{warning['message']}</li>"
                
                warnings_html = f"""
                    <div class="preview-warnings">
                        <h4>⚠ Warnings</h4>
                        <ul>{warnings_list}</ul>
                    </div>
                """

            completion = preview["completion_score"]
            grade_class = f"grade-{completion['grade'].lower()}"
            
            html += f"""
                <div class="object-preview">
                    <div class="preview-header">
                        <h2>{preview['object_name']} <span class="priority-badge priority-{preview['priority_phase']}">{preview['priority_phase']}</span></h2>
                        <div class="completion-score {grade_class}">
                            <span class="score">{completion['percentage']}%</span>
                            <span class="grade">Grade {completion['grade']}</span>
                        </div>
                    </div>
                    
                    {warnings_html}
                    
                    <div class="preview-tabs">
                        <div class="preview-section">
                            <h3>📱 Card View</h3>
                            {preview['card']['html']}
                        </div>
                        
                        <div class="preview-section">
                            <h3>📄 Detail View</h3>
                            {preview['detail']['html']}
                        </div>
                        
                        <div class="preview-section">
                            <h3>📋 List View</h3>
                            {preview['list']['html']}
                        </div>
                        
                        <div class="preview-section">
                            <h3>🏠 Landing View</h3>
                            {preview['landing']['html']}
                        </div>
                    </div>
                </div>
            """

        return html

    def _get_export_html_template(self) -> str:
        """Get HTML template for export."""
        
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDLL Previews - {project_name}</title>
    <style>
        {css_styles}
    </style>
</head>
<body>
    <div class="export-container">
        <header class="export-header">
            <h1>CDLL Previews: {project_name}</h1>
            <p class="project-description">{project_description}</p>
            <p class="export-info">Generated from OOUX ORCA domain model</p>
        </header>
        
        <main class="export-content">
            {previews_html}
        </main>
        
        <footer class="export-footer">
            <p>Generated by OOUX ORCA Project Builder</p>
        </footer>
    </div>
</body>
</html>"""

    def _get_preview_css_styles(self) -> str:
        """Get CSS styles for previews."""
        
        return """
        /* Base Styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8fafc;
        }
        
        .export-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .export-header {
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .export-header h1 {
            color: #1f2937;
            margin-bottom: 1rem;
        }
        
        .project-description {
            color: #6b7280;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }
        
        .export-info {
            color: #9ca3af;
            font-style: italic;
        }
        
        /* Object Preview Container */
        .object-preview {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 3rem;
            overflow: hidden;
        }
        
        .preview-header {
            padding: 1.5rem 2rem;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f9fafb;
        }
        
        .preview-header h2 {
            color: #1f2937;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .priority-badge {
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        .priority-now { background: #dc2626; color: white; }
        .priority-next { background: #ea580c; color: white; }
        .priority-later { background: #0891b2; color: white; }
        .priority-unassigned { background: #6b7280; color: white; }
        
        .completion-score {
            text-align: right;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-weight: 600;
        }
        
        .grade-a { background: #dcfce7; color: #166534; }
        .grade-b { background: #dbeafe; color: #1e40af; }
        .grade-c { background: #fef3c7; color: #92400e; }
        .grade-d { background: #fed7aa; color: #9a3412; }
        .grade-f { background: #fecaca; color: #991b1b; }
        
        .score {
            display: block;
            font-size: 1.2rem;
        }
        
        .grade {
            font-size: 0.8rem;
            opacity: 0.8;
        }
        
        /* Warnings */
        .preview-warnings {
            padding: 1rem 2rem;
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
        }
        
        .preview-warnings h4 {
            color: #92400e;
            margin-bottom: 0.5rem;
        }
        
        .preview-warnings ul {
            color: #78350f;
            margin-left: 1.5rem;
        }
        
        /* Preview Sections */
        .preview-tabs {
            padding: 2rem;
        }
        
        .preview-section {
            margin-bottom: 3rem;
        }
        
        .preview-section h3 {
            color: #374151;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e5e7eb;
        }
        
        /* Card Styles */
        .object-card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            max-width: 350px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .card-header {
            padding: 1rem;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .card-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }
        
        .card-subtitle {
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        .card-body {
            padding: 1rem;
        }
        
        .card-attribute {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }
        
        .attr-label {
            font-weight: 500;
            color: #374151;
        }
        
        .attr-value {
            color: #6b7280;
        }
        
        .card-action {
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #e5e7eb;
        }
        
        /* Detail Styles */
        .object-detail {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .detail-header {
            padding: 1.5rem;
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .detail-title {
            color: #1f2937;
            margin-bottom: 0.5rem;
        }
        
        .detail-definition {
            color: #6b7280;
        }
        
        .detail-section {
            padding: 1.5rem;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .detail-section:last-child {
            border-bottom: none;
        }
        
        .detail-section h3 {
            color: #374151;
            margin-bottom: 1rem;
        }
        
        .detail-attribute {
            margin-bottom: 1rem;
            padding: 0.75rem;
            background: #f9fafb;
            border-radius: 6px;
        }
        
        .attr-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.25rem;
        }
        
        .attr-name {
            font-weight: 600;
            color: #1f2937;
        }
        
        .attr-type {
            color: #6b7280;
            font-size: 0.8rem;
        }
        
        .core-badge, .required-badge {
            font-size: 0.6rem;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        .core-badge {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .required-badge {
            background: #fecaca;
            color: #991b1b;
        }
        
        .detail-action {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: #f9fafb;
            border-radius: 6px;
        }
        
        .detail-action.primary {
            background: #eff6ff;
            border: 1px solid #dbeafe;
        }
        
        .crud-badge {
            font-size: 0.7rem;
            padding: 0.3rem 0.6rem;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: 600;
            color: white;
        }
        
        .crud-create { background: #059669; }
        .crud-read { background: #0891b2; }
        .crud-update { background: #ea580c; }
        .crud-delete { background: #dc2626; }
        .crud-none { background: #6b7280; }
        
        /* List Styles */
        .object-list {
            overflow-x: auto;
        }
        
        .list-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .list-table th {
            background: #f9fafb;
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            color: #374151;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .list-table td {
            padding: 0.75rem;
            border-bottom: 1px solid #f3f4f6;
            color: #6b7280;
        }
        
        .list-table tr:last-child td {
            border-bottom: none;
        }
        
        /* Landing Styles */
        .object-landing {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .landing-header {
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .landing-title {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .landing-description {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .landing-summary, .landing-actions {
            padding: 1.5rem 2rem;
        }
        
        .landing-summary {
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .landing-attributes {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .landing-attribute {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        
        .action-groups {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-top: 1rem;
        }
        
        .action-group {
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 1rem;
            background: #f9fafb;
        }
        
        .group-title {
            color: #374151;
            font-size: 1rem;
            margin-bottom: 0.75rem;
        }
        
        .group-actions {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .landing-action {
            padding: 0.75rem 1rem;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background: white;
            color: #374151;
            text-align: left;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .landing-action:hover {
            background: #f3f4f6;
            border-color: #9ca3af;
        }
        
        .landing-action.primary {
            background: #3b82f6;
            color: white;
            border-color: #2563eb;
        }
        
        .landing-action.primary:hover {
            background: #2563eb;
        }
        
        /* Button Styles */
        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: #3b82f6;
            color: white;
        }
        
        .btn-primary:hover {
            background: #2563eb;
        }
        
        /* Footer */
        .export-footer {
            text-align: center;
            padding: 2rem;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
            margin-top: 2rem;
        }
        
        /* Error Styles */
        .preview-error {
            background: #fef2f2;
            border: 1px solid #fca5a5;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .preview-error h2 {
            color: #991b1b;
            margin-bottom: 0.5rem;
        }
        
        .error-message {
            color: #7f1d1d;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .export-container {
                padding: 1rem;
            }
            
            .preview-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
            
            .landing-attributes {
                grid-template-columns: 1fr;
            }
            
            .action-groups {
                grid-template-columns: 1fr;
            }
        }
        """
