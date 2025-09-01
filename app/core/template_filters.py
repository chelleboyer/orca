"""
Template filters for dashboard and UI formatting
"""

from datetime import datetime
from typing import Optional
import re


def format_section_name(section_id: str) -> str:
    """Format section ID into human-readable name"""
    section_names = {
        'object_catalog': 'Object Catalog',
        'nom_matrix': 'Noun-Object-Metadata Matrix',
        'cta_catalog': 'Call-to-Action Catalog',
        'attribute_catalog': 'Attribute Catalog',
        'wireframes': 'Wireframes',
        'prototypes': 'Prototypes',
        'user_flows': 'User Flows',
        'content_strategy': 'Content Strategy'
    }
    
    return section_names.get(section_id, section_id.replace('_', ' ').title())


def format_datetime(dt: Optional[str]) -> str:
    """Format datetime string for display"""
    if not dt:
        return 'Never'
    
    try:
        # Parse ISO format datetime string
        if isinstance(dt, str):
            # Handle various datetime formats
            if 'T' in dt:
                parsed_dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            else:
                parsed_dt = datetime.fromisoformat(dt)
        else:
            parsed_dt = dt
        
        now = datetime.now(parsed_dt.tzinfo) if parsed_dt.tzinfo else datetime.now()
        diff = now - parsed_dt
        
        # Format relative time
        if diff.days > 7:
            return parsed_dt.strftime('%b %d, %Y')
        elif diff.days > 0:
            return f'{diff.days} days ago'
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f'{hours} hours ago'
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f'{minutes} minutes ago'
        else:
            return 'Just now'
            
    except (ValueError, TypeError):
        return str(dt) if dt else 'Never'


def format_role_color(role: str) -> str:
    """Get CSS class for role styling"""
    role_colors = {
        'owner': 'role-owner',
        'facilitator': 'role-facilitator', 
        'contributor': 'role-contributor',
        'viewer': 'role-viewer'
    }
    return role_colors.get(role.lower(), 'role-viewer')


def format_status_icon(status: str) -> str:
    """Get icon class for status"""
    status_icons = {
        'complete': 'icon-check-circle',
        'in_progress': 'icon-clock',
        'not_started': 'icon-circle',
        'blocked': 'icon-alert-circle'
    }
    return status_icons.get(status, 'icon-circle')


def format_activity_icon(activity_type: str) -> str:
    """Get icon class for activity type"""
    activity_icons = {
        'object_created': 'icon-plus-circle',
        'object_updated': 'icon-edit',
        'object_deleted': 'icon-trash',
        'relationship_created': 'icon-link',
        'relationship_updated': 'icon-link',
        'cta_created': 'icon-zap',
        'cta_updated': 'icon-zap',
        'attribute_created': 'icon-tag',
        'attribute_updated': 'icon-tag',
        'member_joined': 'icon-user-plus',
        'member_left': 'icon-user-minus',
        'project_updated': 'icon-settings',
        'export_generated': 'icon-download'
    }
    return activity_icons.get(activity_type, 'icon-activity')


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """Pluralize a word based on count"""
    if plural is None:
        plural = singular + 's'
    return singular if count == 1 else plural


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size_float = float(size_bytes)
    while size_float >= 1024 and i < len(size_names) - 1:
        size_float /= 1024.0
        i += 1
    
    return f"{size_float:.1f} {size_names[i]}"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + '...'


def format_percentage(value: float) -> str:
    """Format a decimal as percentage"""
    return f"{value * 100:.0f}%"


def format_project_status(status: str) -> str:
    """Format project status for display"""
    status_names = {
        'active': 'Active',
        'archived': 'Archived',
        'template': 'Template',
        'draft': 'Draft'
    }
    return status_names.get(status, status.title())


def get_avatar_url(user_id: str, name: str) -> str:
    """Generate avatar URL for user"""
    # For now, use a simple pattern - in production this might be a service
    # or uploaded avatar
    return f"/api/v1/users/{user_id}/avatar"


def format_slug(text: str) -> str:
    """Convert text to URL-friendly slug"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


# Dictionary of all filters for easy registration
TEMPLATE_FILTERS = {
    'format_section_name': format_section_name,
    'format_datetime': format_datetime,
    'format_role_color': format_role_color,
    'format_status_icon': format_status_icon,
    'format_activity_icon': format_activity_icon,
    'pluralize': pluralize,
    'format_file_size': format_file_size,
    'truncate_text': truncate_text,
    'format_percentage': format_percentage,
    'format_project_status': format_project_status,
    'get_avatar_url': get_avatar_url,
    'format_slug': format_slug
}
