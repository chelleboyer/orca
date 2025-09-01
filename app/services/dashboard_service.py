"""
Dashboard service for aggregating project data and statistics
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models import User, Project, ProjectMember, ProjectInvitation
from app.core.permissions import ProjectPermissions
from app.core.exceptions import NotFoundError, PermissionError


class DashboardService:
    """Service for aggregating dashboard data and statistics"""

    def __init__(self, db: Session):
        self.db = db

    def get_project_dashboard_data(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for a project
        
        Args:
            project_id: The project ID
            user_id: The requesting user ID
            
        Returns:
            Dictionary with complete dashboard data
            
        Raises:
            NotFoundError: If project not found
            PermissionError: If user lacks access
        """
        # Get project and verify access
        project = self._get_project(project_id)
        user_membership = self._get_user_membership(user_id, project_id)
        
        if not user_membership:
            raise PermissionError("Access denied: Not a member of this project")

        # Build comprehensive dashboard data
        dashboard_data = {
            "project": self._get_project_metadata(project),
            "current_user_role": user_membership.role,
            "permissions": ProjectPermissions.get_permissions_for_role(user_membership.role),
            "team_members": self._get_team_members(project_id),
            "orca_progress": self._get_orca_progress(project_id),
            "recent_activity": self._get_recent_activity(project_id),
            "project_statistics": self._get_project_statistics(project_id),
            "pending_invitations": self._get_pending_invitations(project_id, user_membership.role)
        }
        
        return dashboard_data

    def get_user_projects_list(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Get list of projects user has access to
        
        Args:
            user_id: The user ID
            
        Returns:
            List of project summaries for navigation
        """
        # Get all projects user is a member of
        memberships = self.db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.status == "active"
        ).all()
        
        projects = []
        for membership in memberships:
            project = membership.project
            if project and project.status == "active":
                projects.append({
                    "id": str(project.id),
                    "title": project.title,
                    "slug": project.slug,
                    "description": project.description,
                    "role": membership.role,
                    "last_activity": project.last_activity.isoformat() if project.last_activity else None,
                    "member_count": self._get_member_count(project.id),
                    "progress_percentage": self._calculate_overall_progress(project.id)
                })
        
        # Sort by last activity (most recent first)
        projects.sort(key=lambda p: p["last_activity"] or "", reverse=True)
        
        return projects

    def update_project_activity(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Update project last activity timestamp
        
        Args:
            project_id: The project ID
            user_id: The user performing the activity
        """
        project = self._get_project(project_id)
        project.update_activity()
        self.db.commit()

    def get_project_navigation_data(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Get navigation structure and progress for OOUX methodology
        
        Args:
            project_id: The project ID
            user_id: The user ID
            
        Returns:
            Navigation structure with progress indicators
        """
        user_membership = self._get_user_membership(user_id, project_id)
        if not user_membership:
            raise PermissionError("Access denied: Not a member of this project")

        # OOUX methodology navigation structure
        navigation_sections = [
            {
                "id": "object_catalog",
                "name": "Object Catalog",
                "description": "Define and categorize your system objects",
                "route": f"/projects/{project_id}/objects",
                "icon": "cube",
                "required_permission": "view_content",
                "can_edit": ProjectPermissions.has_permission(user_membership.role, "create_objects")
            },
            {
                "id": "nom_matrix",
                "name": "NOM (Nested Object Matrix)",
                "description": "Map object relationships and hierarchy",
                "route": f"/projects/{project_id}/relationships",
                "icon": "hierarchy",
                "required_permission": "view_content",
                "can_edit": ProjectPermissions.has_permission(user_membership.role, "create_relationships")
            },
            {
                "id": "cta_matrix",
                "name": "CTA Matrix",
                "description": "Define calls-to-action and user interactions",
                "route": f"/projects/{project_id}/ctas",
                "icon": "click",
                "required_permission": "view_content",
                "can_edit": ProjectPermissions.has_permission(user_membership.role, "create_ctas")
            },
            {
                "id": "object_map",
                "name": "Object Map",
                "description": "Visualize object relationships and flows",
                "route": f"/projects/{project_id}/map",
                "icon": "map",
                "required_permission": "view_content",
                "can_edit": ProjectPermissions.has_permission(user_membership.role, "edit_objects")
            },
            {
                "id": "cdll",
                "name": "CDLL (Content, Data, Links, Layout)",
                "description": "Define detailed object specifications",
                "route": f"/projects/{project_id}/cdll",
                "icon": "list",
                "required_permission": "view_content",
                "can_edit": ProjectPermissions.has_permission(user_membership.role, "edit_objects")
            }
        ]

        # Add progress data to each section
        orca_progress = self._get_orca_progress(project_id)
        for section in navigation_sections:
            section_progress = orca_progress.get(section["id"], {})
            section.update({
                "status": section_progress.get("status", "not_started"),
                "progress_percentage": section_progress.get("progress_percentage", 0),
                "artifact_count": section_progress.get("artifact_count", 0),
                "last_updated": section_progress.get("last_updated")
            })

        return {
            "sections": navigation_sections,
            "user_role": user_membership.role,
            "overall_progress": self._calculate_overall_progress(project_id)
        }

    # Private helper methods

    def _get_project(self, project_id: uuid.UUID) -> Project:
        """Get project or raise NotFoundError"""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.status != "deleted"
        ).first()
        if not project:
            raise NotFoundError("Project not found")
        return project

    def _get_user_membership(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID
    ) -> Optional[ProjectMember]:
        """Get user's membership in project"""
        return self.db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id,
            ProjectMember.status == "active"
        ).first()

    def _get_project_metadata(self, project: Project) -> Dict[str, Any]:
        """Get project metadata for dashboard"""
        return {
            "id": str(project.id),
            "title": project.title,
            "description": project.description,
            "slug": project.slug,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "last_activity": project.last_activity.isoformat() if project.last_activity else None,
            "status": project.status,
            "owner": {
                "id": str(project.creator.id),
                "name": project.creator.name,
                "email": project.creator.email
            } if project.creator else None
        }

    def _get_team_members(self, project_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get team members with their details"""
        members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.status == "active"
        ).order_by(
            # Owner first, then facilitators, then others
            func.case(
                (ProjectMember.role == "owner", 1),
                (ProjectMember.role == "facilitator", 2),
                (ProjectMember.role == "contributor", 3),
                else_=4
            ),
            ProjectMember.joined_at
        ).all()

        team_data = []
        for member in members:
            if member.user:
                team_data.append({
                    "user_id": str(member.user_id),
                    "name": member.user.name,
                    "email": member.user.email,
                    "role": member.role,
                    "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                    "invited_by": {
                        "id": str(member.inviter.id),
                        "name": member.inviter.name
                    } if member.inviter else None,
                    "last_active": self._get_user_last_activity(member.user_id, project_id),
                    "avatar_url": f"/api/v1/users/{member.user_id}/avatar",  # Placeholder
                    "permissions": ProjectPermissions.get_permissions_for_role(member.role)
                })

        return team_data

    def _get_orca_progress(self, project_id: uuid.UUID) -> Dict[str, Dict[str, Any]]:
        """Get OOUX methodology progress for each section"""
        # This is a placeholder implementation
        # In future stories, this will query actual OOUX artifacts
        
        # For now, simulate progress based on project age and activity
        project = self._get_project(project_id)
        days_since_creation = (datetime.utcnow() - project.created_at).days
        
        # Simulate realistic progress based on project maturity
        sections = {
            "object_catalog": {
                "status": "complete" if days_since_creation > 3 else "in_progress" if days_since_creation > 1 else "not_started",
                "progress_percentage": min(100, days_since_creation * 25),
                "artifact_count": min(15, days_since_creation * 3),
                "last_updated": project.last_activity.isoformat() if project.last_activity else None
            },
            "nom_matrix": {
                "status": "in_progress" if days_since_creation > 2 else "not_started",
                "progress_percentage": max(0, min(75, (days_since_creation - 2) * 25)),
                "artifact_count": max(0, min(23, (days_since_creation - 2) * 6)),
                "last_updated": project.last_activity.isoformat() if days_since_creation > 2 else None
            },
            "cta_matrix": {
                "status": "not_started",
                "progress_percentage": 0,
                "artifact_count": 0,
                "last_updated": None
            },
            "object_map": {
                "status": "not_started",
                "progress_percentage": 0,
                "artifact_count": 0,
                "last_updated": None
            },
            "cdll": {
                "status": "not_started",
                "progress_percentage": 0,
                "artifact_count": 0,
                "last_updated": None
            }
        }

        return sections

    def _get_recent_activity(self, project_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get recent project activity"""
        # This is a placeholder implementation
        # In a real system, this would query an activity log table
        
        activities = [
            {
                "id": str(uuid.uuid4()),
                "type": "member_joined",
                "user": "System",
                "description": "Project created and initial member added",
                "timestamp": datetime.utcnow().isoformat(),
                "artifact_id": None
            }
        ]

        # Add invitation activities
        recent_invitations = self.db.query(ProjectInvitation).filter(
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.sent_at > datetime.utcnow() - timedelta(days=7)
        ).order_by(desc(ProjectInvitation.sent_at)).limit(5).all()

        for invitation in recent_invitations:
            activities.append({
                "id": str(invitation.id),
                "type": "invitation_sent",
                "user": invitation.inviter.name if invitation.inviter else "System",
                "description": f"Invited {invitation.email} as {invitation.role}",
                "timestamp": invitation.sent_at.isoformat(),
                "artifact_id": str(invitation.id)
            })

        # Sort by timestamp (most recent first)
        activities.sort(key=lambda a: a["timestamp"], reverse=True)
        
        return activities[:10]  # Return last 10 activities

    def _get_project_statistics(self, project_id: uuid.UUID) -> Dict[str, Any]:
        """Get project statistics"""
        member_count = self._get_member_count(project_id)
        
        # In future stories, these will be real counts from OOUX artifact tables
        return {
            "total_objects": 0,  # Will be real count in future stories
            "total_relationships": 0,  # Will be real count in future stories  
            "total_ctas": 0,  # Will be real count in future stories
            "total_attributes": 0,  # Will be real count in future stories
            "team_size": member_count,
            "pending_invitations": self._get_pending_invitation_count(project_id)
        }

    def _get_pending_invitations(
        self,
        project_id: uuid.UUID,
        user_role: str
    ) -> List[Dict[str, Any]]:
        """Get pending invitations if user has permission"""
        if not ProjectPermissions.has_permission(user_role, "view_members"):
            return []

        invitations = self.db.query(ProjectInvitation).filter(
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.status == "pending",
            ProjectInvitation.expires_at > datetime.utcnow()
        ).order_by(desc(ProjectInvitation.sent_at)).all()

        return [invitation.to_dict() for invitation in invitations]

    def _get_member_count(self, project_id: uuid.UUID) -> int:
        """Get count of active members"""
        return self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.status == "active"
        ).count()

    def _get_pending_invitation_count(self, project_id: uuid.UUID) -> int:
        """Get count of pending invitations"""
        return self.db.query(ProjectInvitation).filter(
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.status == "pending",
            ProjectInvitation.expires_at > datetime.utcnow()
        ).count()

    def _get_user_last_activity(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID
    ) -> Optional[str]:
        """Get user's last activity in project (placeholder)"""
        # In a real system, this would query an activity log
        # For now, return a recent timestamp
        return datetime.utcnow().isoformat()

    def _calculate_overall_progress(self, project_id: uuid.UUID) -> int:
        """Calculate overall project progress percentage"""
        orca_progress = self._get_orca_progress(project_id)
        
        total_progress = 0
        section_count = len(orca_progress)
        
        for section_data in orca_progress.values():
            total_progress += section_data.get("progress_percentage", 0)
        
        return int(total_progress / section_count) if section_count > 0 else 0
