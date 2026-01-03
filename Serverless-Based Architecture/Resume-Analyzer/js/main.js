
let isAuthenticated = false;
let currentUser = null;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    console.log(' Main.js initializing...');
    
    // Set current year in footer
    const yearElement = document.getElementById('currentYear');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }
    
    // Check authentication status
    checkAuthStatus();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load any messages from URL parameters
    displayMessagesFromURL();
    
    // Add smooth scrolling and animations
    setupSmoothScrolling();
    setupScrollAnimations();
    
    console.log(' Main.js initialized');
});

// Check if user is authenticated
function checkAuthStatus() {
    // First check if we have Cognito tokens (priority)
    if (window.CognitoAuth && window.CognitoAuth.isAuthenticated()) {
        currentUser = window.CognitoAuth.getCurrentUser();
        isAuthenticated = true;
        updateUIForAuthenticatedUser();
        console.log(' User authenticated:', currentUser?.email);
        return;
    }
    
    // Fallback: Check localStorage for user session
    const userSession = localStorage.getItem('userSession');
    
    if (userSession) {
        try {
            currentUser = JSON.parse(userSession);
            isAuthenticated = true;
            updateUIForAuthenticatedUser();
            console.log(' User session found:', currentUser?.email);
        } catch (e) {
            console.error('Error parsing user session:', e);
            clearAuthSession();
        }
    } else {
        updateUIForUnauthenticatedUser();
        console.log(' No active session');
    }
}

// Update UI for authenticated user
function updateUIForAuthenticatedUser() {
    console.log(' Updating UI for authenticated user');
    
    // Hide login button, show logout button
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const accountNavItem = document.getElementById('accountNavItem');
    
    if (loginBtn) loginBtn.style.display = 'none';
    if (logoutBtn) logoutBtn.style.display = 'block';
    if (accountNavItem) accountNavItem.style.display = 'block';
    
    // Update hero buttons if they exist
    const heroButtons = document.getElementById('heroButtons');
    if (heroButtons) {
        heroButtons.innerHTML = `
            <a href="upload.html" class="btn btn-primary btn-lg px-5">
                <i class="fas fa-upload me-2"></i>Upload Resume
            </a>
            <a href="history.html" class="btn btn-outline-secondary btn-lg px-5">
                <i class="fas fa-history me-2"></i>View History
            </a>
        `;
    }
}

// Update UI for unauthenticated user
function updateUIForUnauthenticatedUser() {
    console.log(' Updating UI for unauthenticated user');
    
    // Show login button, hide logout button
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const accountNavItem = document.getElementById('accountNavItem');
    
    if (loginBtn) loginBtn.style.display = 'block';
    if (logoutBtn) logoutBtn.style.display = 'none';
    if (accountNavItem) accountNavItem.style.display = 'none';
    
    // Update hero buttons if they exist
    const heroButtons = document.getElementById('heroButtons');
    if (heroButtons) {
        heroButtons.innerHTML = `
            <button class="btn btn-primary btn-lg px-5" id="getStartedBtn">
                <i class="fas fa-rocket me-2"></i>Get Started
            </button>
            <a href="about.html" class="btn btn-outline-secondary btn-lg px-5">
                <i class="fas fa-info-circle me-2"></i>Learn More
            </a>
        `;
        
        // Add event listener to "Get Started" button
        const getStartedBtn = document.getElementById('getStartedBtn');
        if (getStartedBtn) {
            getStartedBtn.addEventListener('click', function() {
                displayMessage('Please log in to get started', 'info');
                // Scroll to top where login button is
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }
    }
}

// Setup event listeners
function setupEventListeners() {
    console.log(' Setting up event listeners...');
    
    // Login button
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log(' Login button clicked');
            
            // Use Cognito Hosted UI
            if (window.CognitoAuth && typeof window.CognitoAuth.login === 'function') {
                window.CognitoAuth.login();
            } else {
                console.error(' CognitoAuth not loaded');
                alert('Authentication system not ready. Please refresh the page.');
            }
        });
        console.log(' Login button listener attached');
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log(' Logout button clicked');
            handleLogout();
        });
        console.log(' Logout button listener attached');
    }
}

// Handle logout
function handleLogout() {
    if (window.CognitoAuth && typeof window.CognitoAuth.logout === 'function') {
        // Use Cognito logout (will redirect)
        window.CognitoAuth.logout();
    } else {
        // Fallback logout
        clearAuthSession();
        displayMessage('You have been logged out successfully', 'success');
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);
    }
}

// Clear authentication session
function clearAuthSession() {
    localStorage.removeItem('userSession');
    localStorage.removeItem('idToken');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    isAuthenticated = false;
    currentUser = null;
}

// Display messages from URL parameters
function displayMessagesFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const message = urlParams.get('message');
    const type = urlParams.get('type') || 'info';
    
    if (message) {
        displayMessage(decodeURIComponent(message), type);
        
        // Clean up URL
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
    }
}

// Display a message to the user
function displayMessage(message, type = 'info') {
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) {
        console.warn('Messages container not found');
        return;
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} border-0 rounded-pill mb-3 animate-fade-in`;
    
    // Set colors based on type
    let bgColor, borderColor, icon;
    switch(type) {
        case 'success':
            bgColor = 'rgba(25, 135, 84, 0.1)';
            borderColor = '#198754';
            icon = 'fa-check-circle';
            break;
        case 'danger':
        case 'error':
            bgColor = 'rgba(220, 53, 69, 0.1)';
            borderColor = '#dc3545';
            icon = 'fa-exclamation-circle';
            break;
        case 'warning':
            bgColor = 'rgba(255, 193, 7, 0.1)';
            borderColor = '#ffc107';
            icon = 'fa-exclamation-triangle';
            break;
        default:
            bgColor = 'rgba(13, 202, 240, 0.1)';
            borderColor = '#0dcaf0';
            icon = 'fa-info-circle';
    }
    
    alertDiv.style.cssText = `background: ${bgColor}; border-left: 4px solid ${borderColor};`;
    alertDiv.innerHTML = `<i class="fas ${icon} me-2"></i>${message}`;
    
    messagesContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.style.opacity = '0';
        alertDiv.style.transition = 'opacity 0.3s';
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

// Setup smooth scrolling for anchor links
function setupSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            
            // Only handle pure hash links
            if (!href || !href.startsWith('#') || href.length <= 1) {
                return;
            }
            
            e.preventDefault();
            
            try {
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            } catch (err) {
                // Invalid selector, ignore
            }
        });
    });
}

// Setup scroll animations
function setupScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
            }
        });
    }, observerOptions);
    
    // Observe all cards and sections
    document.querySelectorAll('.card, section').forEach(element => {
        observer.observe(element);
    });
}

// Save user session
function saveUserSession(userData) {
    localStorage.setItem('userSession', JSON.stringify(userData));
    currentUser = userData;
    isAuthenticated = true;
}

// Get current user
function getCurrentUser() {
    if (window.CognitoAuth) {
        return window.CognitoAuth.getCurrentUser() || currentUser;
    }
    return currentUser;
}

// Check if user is authenticated
function isUserAuthenticated() {
    if (window.CognitoAuth) {
        return window.CognitoAuth.isAuthenticated();
    }
    return isAuthenticated;
}

// Export functions for use in other scripts
window.ResumeAnalyzer = {
    saveUserSession,
    getCurrentUser,
    isUserAuthenticated,
    clearAuthSession,
    displayMessage,
    checkAuthStatus
};

console.log('ResumeAnalyzer object exported');