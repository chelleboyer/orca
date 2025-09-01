/**
 * Dashboard JavaScript functionality
 */

// Global variables
let currentProjectId = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

function initializeDashboard() {
    // Extract project ID from URL
    const pathParts = window.location.pathname.split('/');
    const projectIndex = pathParts.indexOf('projects');
    if (projectIndex !== -1 && pathParts[projectIndex + 1]) {
        currentProjectId = pathParts[projectIndex + 1];
    }
    
    // Initialize tooltips and interactive elements
    initializeTooltips();
    initializeProgressCards();
    
    // Set up periodic refresh for activity feed
    setInterval(refreshActivityFeed, 30000); // Refresh every 30 seconds
}

function initializeTooltips() {
    // Add tooltips to progress cards and other elements
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function initializeProgressCards() {
    // Add click handlers to progress cards
    const progressCards = document.querySelectorAll('.progress-card');
    progressCards.forEach(card => {
        card.addEventListener('click', function() {
            const sectionId = this.dataset.sectionId;
            if (sectionId) {
                navigateToSection(sectionId);
            }
        });
    });
    
    // Set progress bar widths from data attributes
    const progressFills = document.querySelectorAll('.progress-fill[data-progress]');
    progressFills.forEach(fill => {
        const progress = fill.dataset.progress;
        if (progress !== undefined) {
            fill.style.width = progress + '%';
        }
    });
}

// Navigation functions
function navigateToSection(sectionId) {
    if (!currentProjectId) {
        console.error('Project ID not found');
        return;
    }
    
    const sectionRoutes = {
        'object_catalog': '/objects',
        'nom_matrix': '/relationships',
        'cta_catalog': '/ctas',
        'attribute_catalog': '/attributes',
        'wireframes': '/wireframes',
        'prototypes': '/prototypes'
    };
    
    const route = sectionRoutes[sectionId];
    if (route) {
        window.location.href = `/projects/${currentProjectId}${route}`;
    } else {
        console.warn(`Unknown section: ${sectionId}`);
    }
}

function editProject() {
    if (!currentProjectId) {
        console.error('Project ID not found');
        return;
    }
    
    window.location.href = `/projects/${currentProjectId}/settings`;
}

function startWorking() {
    // Navigate to the first incomplete section
    const progressCards = document.querySelectorAll('.progress-card');
    for (const card of progressCards) {
        if (!card.classList.contains('complete')) {
            const sectionId = card.dataset.sectionId;
            if (sectionId) {
                navigateToSection(sectionId);
                return;
            }
        }
    }
    
    // If all sections are complete, go to objects by default
    navigateToSection('object_catalog');
}

// Invitation management
function showInviteModal() {
    const modal = document.getElementById('inviteModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Focus on email input
        const emailInput = document.getElementById('inviteEmail');
        if (emailInput) {
            setTimeout(() => emailInput.focus(), 100);
        }
    }
}

function hideInviteModal() {
    const modal = document.getElementById('inviteModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        
        // Reset form
        const form = document.getElementById('inviteForm');
        if (form) {
            form.reset();
        }
    }
}

async function sendInvitation(event) {
    event.preventDefault();
    
    if (!currentProjectId) {
        showError('Project ID not found');
        return;
    }
    
    const form = event.target;
    const formData = new FormData(form);
    const invitationData = {
        email: formData.get('email'),
        role: formData.get('role')
    };
    
    // Show loading state
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Sending...';
    submitButton.disabled = true;
    
    try {
        const response = await fetch(`/api/v1/projects/${currentProjectId}/invitations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify(invitationData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showSuccess('Invitation sent successfully!');
            hideInviteModal();
            
            // Refresh the page to show the new pending invitation
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const error = await response.json();
            showError(error.detail || 'Failed to send invitation');
        }
    } catch (error) {
        console.error('Error sending invitation:', error);
        showError('Failed to send invitation. Please try again.');
    } finally {
        // Restore button state
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    }
}

async function cancelInvitation(invitationId) {
    if (!confirm('Are you sure you want to cancel this invitation?')) {
        return;
    }
    
    if (!currentProjectId) {
        showError('Project ID not found');
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/projects/${currentProjectId}/invitations/${invitationId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (response.ok) {
            showSuccess('Invitation cancelled successfully!');
            
            // Remove the invitation card from DOM
            const invitationCard = document.querySelector(`[data-invitation-id="${invitationId}"]`);
            if (invitationCard) {
                invitationCard.remove();
            }
            
            // Refresh the page to update counts
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const error = await response.json();
            showError(error.detail || 'Failed to cancel invitation');
        }
    } catch (error) {
        console.error('Error cancelling invitation:', error);
        showError('Failed to cancel invitation. Please try again.');
    }
}

// Member management
function manageMember(userId) {
    // For now, redirect to project settings where member management should be
    window.location.href = `/projects/${currentProjectId}/settings#members`;
}

// Activity feed
async function refreshActivityFeed() {
    if (!currentProjectId) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/projects/${currentProjectId}/activity`, {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateActivityFeed(data.activities);
        }
    } catch (error) {
        console.error('Error refreshing activity feed:', error);
    }
}

function updateActivityFeed(activities) {
    const activityFeed = document.querySelector('.activity-feed');
    if (!activityFeed || !activities) {
        return;
    }
    
    // Only update if there are new activities
    const currentActivityCount = activityFeed.children.length;
    if (activities.length <= currentActivityCount) {
        return;
    }
    
    // Create new activity items
    activities.slice(currentActivityCount).forEach(activity => {
        const activityItem = createActivityItem(activity);
        activityFeed.insertBefore(activityItem, activityFeed.firstChild);
    });
}

function createActivityItem(activity) {
    const div = document.createElement('div');
    div.className = 'activity-item';
    div.innerHTML = `
        <div class="activity-icon">
            <i class="icon-${activity.type}"></i>
        </div>
        <div class="activity-content">
            <div class="activity-description">${escapeHtml(activity.description)}</div>
            <div class="activity-meta">
                <span class="activity-user">${escapeHtml(activity.user)}</span>
                <span class="activity-time">${formatDateTime(activity.timestamp)}</span>
            </div>
        </div>
        ${activity.artifact_id ? `
            <button class="btn-link" onclick="viewArtifact('${activity.artifact_id}')">
                View →
            </button>
        ` : ''}
    `;
    return div;
}

function viewArtifact(artifactId) {
    // Navigate to the specific artifact
    window.location.href = `/artifacts/${artifactId}`;
}

// Utility functions
function getAuthToken() {
    // Get JWT token from localStorage or sessionStorage
    return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token') || '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = diffMs / (1000 * 60 * 60);
    const diffDays = diffHours / 24;
    
    if (diffHours < 1) {
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        return `${diffMinutes}m ago`;
    } else if (diffHours < 24) {
        return `${Math.floor(diffHours)}h ago`;
    } else if (diffDays < 7) {
        return `${Math.floor(diffDays)}d ago`;
    } else {
        return date.toLocaleDateString();
    }
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'error');
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${escapeHtml(message)}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    
    // Add to page
    let notificationContainer = document.querySelector('.notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.className = 'notification-container';
        document.body.appendChild(notificationContainer);
    }
    
    notificationContainer.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function showTooltip(event) {
    const element = event.target;
    const tooltipText = element.dataset.tooltip;
    if (!tooltipText) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = tooltipText;
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.position = 'absolute';
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
    tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
    tooltip.style.zIndex = '1000';
    tooltip.style.background = '#1a202c';
    tooltip.style.color = 'white';
    tooltip.style.padding = '0.5rem';
    tooltip.style.borderRadius = '0.25rem';
    tooltip.style.fontSize = '0.875rem';
    tooltip.style.whiteSpace = 'nowrap';
    
    element._tooltip = tooltip;
}

function hideTooltip(event) {
    const element = event.target;
    if (element._tooltip) {
        element._tooltip.remove();
        delete element._tooltip;
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Escape key to close modals
    if (event.key === 'Escape') {
        hideInviteModal();
    }
    
    // Ctrl/Cmd + I to invite member (if user has permission)
    if ((event.ctrlKey || event.metaKey) && event.key === 'i') {
        event.preventDefault();
        const inviteButton = document.querySelector('[onclick="showInviteModal()"]');
        if (inviteButton) {
            showInviteModal();
        }
    }
});

// Handle modal clicks outside content
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        hideInviteModal();
    }
});
