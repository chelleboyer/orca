/**
 * Base JavaScript functionality
 */

// Global utilities
window.App = {
    // Configuration
    config: {
        apiBaseUrl: '/api/v1',
        version: '1.0.0'
    },
    
    // Utilities
    utils: {
        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },
        
        formatDateTime: function(timestamp) {
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
        },
        
        getAuthToken: function() {
            return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token') || '';
        },
        
        setAuthToken: function(token, remember = false) {
            if (remember) {
                localStorage.setItem('auth_token', token);
            } else {
                sessionStorage.setItem('auth_token', token);
            }
        },
        
        clearAuthToken: function() {
            localStorage.removeItem('auth_token');
            sessionStorage.removeItem('auth_token');
        }
    },
    
    // API utilities
    api: {
        request: async function(endpoint, options = {}) {
            const url = App.config.apiBaseUrl + endpoint;
            const token = App.utils.getAuthToken();
            
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                }
            };
            
            const mergedOptions = {
                ...defaultOptions,
                ...options,
                headers: {
                    ...defaultOptions.headers,
                    ...options.headers
                }
            };
            
            try {
                const response = await fetch(url, mergedOptions);
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || `HTTP ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('API request failed:', error);
                throw error;
            }
        },
        
        get: function(endpoint) {
            return App.api.request(endpoint, { method: 'GET' });
        },
        
        post: function(endpoint, data) {
            return App.api.request(endpoint, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },
        
        put: function(endpoint, data) {
            return App.api.request(endpoint, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },
        
        delete: function(endpoint) {
            return App.api.request(endpoint, { method: 'DELETE' });
        }
    },
    
    // Notification system
    notifications: {
        show: function(message, type = 'info') {
            const container = document.querySelector('.notification-container');
            if (!container) {
                console.warn('Notification container not found');
                return;
            }
            
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.innerHTML = `
                <div class="notification-content">
                    <span class="notification-message">${App.utils.escapeHtml(message)}</span>
                    <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
                </div>
            `;
            
            container.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        },
        
        success: function(message) {
            App.notifications.show(message, 'success');
        },
        
        error: function(message) {
            App.notifications.show(message, 'error');
        },
        
        info: function(message) {
            App.notifications.show(message, 'info');
        }
    }
};

// User menu functionality
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) {
        const isVisible = dropdown.style.display !== 'none';
        dropdown.style.display = isVisible ? 'none' : 'block';
    }
}

// Close user menu when clicking outside
document.addEventListener('click', function(event) {
    const userMenu = document.querySelector('.user-menu');
    const dropdown = document.getElementById('userDropdown');
    
    if (userMenu && dropdown && !userMenu.contains(event.target)) {
        dropdown.style.display = 'none';
    }
});

// Authentication check
document.addEventListener('DOMContentLoaded', function() {
    const token = App.utils.getAuthToken();
    const isAuthPage = window.location.pathname.includes('/auth/') || 
                      window.location.pathname === '/login' || 
                      window.location.pathname === '/register';
    const isDemoPage = window.location.pathname.includes('/demo/');
    
    if (!token && !isAuthPage && !isDemoPage) {
        // Redirect to login if no token and not on auth page or demo page
        window.location.href = '/login';
    } else if (token && isAuthPage) {
        // Redirect to dashboard if logged in and on auth page
        window.location.href = '/projects';
    }
});

// Handle logout
function logout() {
    App.utils.clearAuthToken();
    App.notifications.success('Logged out successfully');
    setTimeout(() => {
        window.location.href = '/login';
    }, 1000);
}

// Global error handling
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    App.notifications.error('An unexpected error occurred');
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    App.notifications.error('An unexpected error occurred');
});

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Escape key to close modals and dropdowns
    if (event.key === 'Escape') {
        // Close user dropdown
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
        
        // Close any open modals
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (modal.style.display !== 'none') {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }
});

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('OOUX ORCA Application initialized');
});
