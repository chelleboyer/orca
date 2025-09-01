"""
Project service layer for business logic and operations
"""

import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from math import ceil

from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session, joinedload

from app.models import User, Project, ProjectMember
from app.models.base import generate_slug, generate_unique_slug
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectListRequest,
    ProjectSummary,
    ProjectDetail,
    ProjectResponse,
    ProjectListResponse,
    ProjectStatusResponse,
    ProjectProgress,
    ProjectStatistics,
    UserSummary,
    ProjectMemberResponse,
    PaginationInfo,
    ProjectStatus,
    ProjectMemberRole,
    ProjectMemberStatus
)
from app.core.permissions import (
    check_slug_exists,
    create_project_facilitator_membership,
    get_user_project_membership
)


class ProjectService:
    """Service class for project management operations"""
    
    def __init__(self, db: Session):
        self.db = db

    def create_project(
        self, 
        project_data: ProjectCreateRequest, 
        creator: User
    ) -> Tuple[Project, ProjectMember]:
        """
        Create a new project with the user as facilitator
        
        Args:
            project_data: Project creation data
            creator: User creating the project
            
        Returns:
            Tuple of (Project, ProjectMember) for creator's membership
        """
        # Generate unique slug
        base_slug = generate_slug(project_data.title)
        unique_slug = generate_unique_slug(
            base_slug,
            lambda slug: check_slug_exists(slug, self.db)
        )
        
        # Create project
        project = Project(
            title=project_data.title,
            description=project_data.description,
            slug=unique_slug,
            created_by=creator.id,
            status="active",
            project_metadata={},
            settings={}
        )
        
        self.db.add(project)
        self.db.flush()  # Get the project ID
        
        # Create facilitator membership for creator
        membership = create_project_facilitator_membership(project, creator, self.db)
        
        self.db.commit()
        self.db.refresh(project)
        self.db.refresh(membership)
        
        return project, membership

    def get_project_by_id(self, project_id: uuid.UUID) -> Optional[Project]:
        """Get project by ID"""
        return self.db.query(Project).filter(
            Project.id == project_id,
            Project.status != "deleted"
        ).first()

    def get_project_by_slug(self, slug: str) -> Optional[Project]:
        """Get project by slug"""
        return self.db.query(Project).filter(
            Project.slug == slug,
            Project.status != "deleted"
        ).first()

    def update_project(
        self,
        project: Project,
        project_data: ProjectUpdateRequest,
        user: User
    ) -> Project:
        """
        Update project details
        
        Args:
            project: Project to update
            project_data: Update data
            user: User performing the update
            
        Returns:
            Updated project
        """
        # Update fields if provided
        if project_data.title is not None:
            project.title = project_data.title
            # Regenerate slug if title changed
            base_slug = generate_slug(project_data.title)
            unique_slug = generate_unique_slug(
                base_slug,
                lambda slug: check_slug_exists(slug, self.db, exclude_id=project.id)
            )
            project.slug = unique_slug
        
        if project_data.description is not None:
            project.description = project_data.description
        
        # Update activity
        project.last_activity = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(project)
        
        return project

    def get_user_projects(
        self,
        user: User,
        request_params: ProjectListRequest
    ) -> ProjectListResponse:
        """
        Get paginated list of user's projects
        
        Args:
            user: User to get projects for
            request_params: Search and pagination parameters
            
        Returns:
            Paginated project list response
        """
        # Base query for user's projects
        query = self.db.query(Project).join(
            ProjectMember,
            and_(
                ProjectMember.project_id == Project.id,
                ProjectMember.user_id == user.id,
                ProjectMember.status == "active"
            )
        ).filter(
            Project.status != "deleted"
        )
        
        # Apply filters
        if request_params.search:
            search_term = f"%{request_params.search}%"
            query = query.filter(
                or_(
                    Project.title.ilike(search_term),
                    Project.description.ilike(search_term)
                )
            )
        
        if request_params.status:
            query = query.filter(Project.status == request_params.status.value)
        
        if request_params.my_role:
            query = query.filter(ProjectMember.role == request_params.my_role.value)
        
        # Count total items
        total = query.count()
        
        # Apply pagination and ordering
        query = query.order_by(Project.last_activity.desc())
        offset = (request_params.page - 1) * request_params.per_page
        projects = query.offset(offset).limit(request_params.per_page).all()
        
        # Convert to response format
        project_summaries = []
        for project in projects:
            membership = get_user_project_membership(user, project, self.db)
            if not membership:
                continue  # Skip if user somehow doesn't have membership
                
            member_count = self.get_project_member_count(project.id)
            progress = self.get_project_progress(project.id)
            
            summary = ProjectSummary(
                id=project.id,
                title=project.title,
                description=project.description,
                slug=project.slug,
                status=ProjectStatus(project.status),
                last_activity=project.last_activity,
                created_at=project.created_at,
                updated_at=project.updated_at,
                member_count=member_count,
                my_role=ProjectMemberRole(membership.role),
                progress=progress
            )
            project_summaries.append(summary)
        
        # Create pagination info
        pages = ceil(total / request_params.per_page) if total > 0 else 0
        pagination = PaginationInfo(
            page=request_params.page,
            per_page=request_params.per_page,
            total=total,
            pages=pages
        )
        
        return ProjectListResponse(
            projects=project_summaries,
            pagination=pagination
        )

    def get_project_detail(self, project: Project, user: User) -> ProjectDetail:
        """
        Get detailed project information
        
        Args:
            project: Project to get details for
            user: User requesting details
            
        Returns:
            Detailed project information
        """
        # Get creator info
        creator = self.db.query(User).filter(User.id == project.created_by).first()
        if not creator:
            raise ValueError(f"Creator not found for project {project.id}")
            
        creator_summary = UserSummary(
            id=creator.id,
            name=creator.name,
            email=creator.email
        )
        
        # Get user's membership
        user_membership = get_user_project_membership(user, project, self.db)
        if not user_membership:
            raise ValueError(f"User {user.id} is not a member of project {project.id}")
        
        # Get all project members
        members_query = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.status == "active"
        ).options(joinedload(ProjectMember.user))
        
        member_responses = []
        for member in members_query.all():
            user_summary = UserSummary(
                id=member.user.id,
                name=member.user.name,
                email=member.user.email
            )
            member_response = ProjectMemberResponse(
                id=member.id,
                user=user_summary,
                role=ProjectMemberRole(member.role),
                status=ProjectMemberStatus(member.status),
                invited_at=member.invited_at,
                joined_at=member.joined_at,
                created_at=member.created_at,
                updated_at=member.updated_at
            )
            member_responses.append(member_response)
        
        # Get project progress
        progress = self.get_project_progress(project.id)
        
        return ProjectDetail(
            id=project.id,
            title=project.title,
            description=project.description,
            slug=project.slug,
            status=ProjectStatus(project.status),
            last_activity=project.last_activity,
            created_at=project.created_at,
            updated_at=project.updated_at,
            created_by=creator_summary,
            my_role=ProjectMemberRole(user_membership.role),
            members=member_responses,
            progress=progress
        )

    def get_project_response(self, project: Project, user: User) -> ProjectResponse:
        """
        Get project response for create/update operations
        
        Args:
            project: Project to get response for
            user: User requesting response
            
        Returns:
            Project response
        """
        # Get creator info
        creator = self.db.query(User).filter(User.id == project.created_by).first()
        if not creator:
            raise ValueError(f"Creator not found for project {project.id}")
            
        creator_summary = UserSummary(
            id=creator.id,
            name=creator.name,
            email=creator.email
        )
        
        # Get user's membership
        user_membership = get_user_project_membership(user, project, self.db)
        if not user_membership:
            raise ValueError(f"User {user.id} is not a member of project {project.id}")
        
        # Get member count
        member_count = self.get_project_member_count(project.id)
        
        return ProjectResponse(
            id=project.id,
            title=project.title,
            description=project.description,
            slug=project.slug,
            status=ProjectStatus(project.status),
            last_activity=project.last_activity,
            created_at=project.created_at,
            updated_at=project.updated_at,
            created_by=creator_summary,
            member_count=member_count,
            my_role=ProjectMemberRole(user_membership.role)
        )

    def get_project_status(self, project: Project) -> ProjectStatusResponse:
        """
        Get project status and health information
        
        Args:
            project: Project to get status for
            
        Returns:
            Project status response
        """
        # Calculate project statistics
        member_count = self.get_project_member_count(project.id)
        days_since_creation = (datetime.utcnow() - project.created_at).days
        
        statistics = ProjectStatistics(
            total_objects=0,  # Will be implemented with object models
            total_relationships=0,  # Will be implemented with relationship models
            total_cta_entries=0,  # Will be implemented with CTA models
            completion_percentage=0.0,  # Will be calculated based on artifacts
            active_members=member_count,
            days_since_creation=days_since_creation
        )
        
        # Determine health status
        health = "healthy"
        if days_since_creation > 30 and statistics.completion_percentage == 0:
            health = "warning"
        elif days_since_creation > 90 and statistics.completion_percentage < 25:
            health = "critical"
        
        return ProjectStatusResponse(
            project_id=project.id,
            status=ProjectStatus(project.status),
            health=health,
            last_activity=project.last_activity,
            statistics=statistics,
            recent_activity=[]  # Will be implemented with activity tracking
        )

    def get_project_member_count(self, project_id: uuid.UUID) -> int:
        """Get count of active project members"""
        return self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.status == "active"
        ).count()

    def get_project_progress(self, project_id: uuid.UUID) -> ProjectProgress:
        """
        Get project progress information
        
        Args:
            project_id: Project ID
            
        Returns:
            Project progress data
        """
        # For now, return empty progress
        # This will be enhanced when OOUX artifact models are implemented
        return ProjectProgress(
            objects=0,
            relationships=0,
            cta_matrix=0,
            overall_completion=0.0
        )

    def archive_project(self, project: Project) -> Project:
        """
        Archive a project
        
        Args:
            project: Project to archive
            
        Returns:
            Archived project
        """
        project.status = "archived"
        project.last_activity = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(project)
        
        return project

    def activate_project(self, project: Project) -> Project:
        """
        Activate an archived project
        
        Args:
            project: Project to activate
            
        Returns:
            Activated project
        """
        project.status = "active"
        project.last_activity = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(project)
        
        return project

    def delete_project(self, project: Project) -> None:
        """
        Soft delete a project
        
        Args:
            project: Project to delete
        """
        project.status = "deleted"
        project.last_activity = datetime.utcnow()
        
        # Also deactivate all memberships
        self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id
        ).update({"status": "inactive"})
        
        self.db.commit()

    def search_projects(
        self,
        user: User,
        search_term: str,
        limit: int = 10
    ) -> List[ProjectSummary]:
        """
        Search projects by title or description
        
        Args:
            user: User performing search
            search_term: Search term
            limit: Maximum results
            
        Returns:
            List of matching projects
        """
        search_pattern = f"%{search_term}%"
        
        query = self.db.query(Project).join(
            ProjectMember,
            and_(
                ProjectMember.project_id == Project.id,
                ProjectMember.user_id == user.id,
                ProjectMember.status == "active"
            )
        ).filter(
            Project.status != "deleted",
            or_(
                Project.title.ilike(search_pattern),
                Project.description.ilike(search_pattern)
            )
        ).order_by(
            Project.last_activity.desc()
        ).limit(limit)
        
        projects = query.all()
        
        project_summaries = []
        for project in projects:
            membership = get_user_project_membership(user, project, self.db)
            if not membership:
                continue  # Skip if user somehow doesn't have membership
                
            member_count = self.get_project_member_count(project.id)
            progress = self.get_project_progress(project.id)
            
            summary = ProjectSummary(
                id=project.id,
                title=project.title,
                description=project.description,
                slug=project.slug,
                status=ProjectStatus(project.status),
                last_activity=project.last_activity,
                created_at=project.created_at,
                updated_at=project.updated_at,
                member_count=member_count,
                my_role=ProjectMemberRole(membership.role),
                progress=progress
            )
            project_summaries.append(summary)
        
        return project_summaries
