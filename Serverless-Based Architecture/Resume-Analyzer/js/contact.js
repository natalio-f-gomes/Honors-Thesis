
const ContactLogger = {
    log: function(message, data = null) {
        const timestamp = new Date().toISOString();
        console.log(`[Contact Form] ${timestamp} - ${message}`, data || '');
    },
    error: function(message, error = null) {
        const timestamp = new Date().toISOString();
        console.error(`[Contact Form ERROR] ${timestamp} - ${message}`, error || '');
    },
    warn: function(message, data = null) {
        const timestamp = new Date().toISOString();
        console.warn(`[Contact Form WARNING] ${timestamp} - ${message}`, data || '');
    },
    info: function(message, data = null) {
        const timestamp = new Date().toISOString();
        console.info(`[Contact Form INFO] ${timestamp} - ${message}`, data || '');
    }
};

document.addEventListener('DOMContentLoaded', function() {
    ContactLogger.log('===== Contact Page Initialization Started =====');
    ContactLogger.log('DOM Content loaded, beginning initialization sequence');
    
    // Set current year
    try {
        const currentYear = new Date().getFullYear();
        const yearElement = document.getElementById('currentYear');
        if (yearElement) {
            yearElement.textContent = currentYear;
            ContactLogger.log(`Current year successfully set to: ${currentYear}`);
        } else {
            ContactLogger.warn('Current year element (#currentYear) not found in DOM');
        }
    } catch (error) {
        ContactLogger.error('Error setting current year', error);
    }
    
    // Pre-fill email if user is authenticated
    ContactLogger.log('Starting user email pre-fill check...');
    prefillUserEmail();
    
    // Setup form submission
    ContactLogger.log('Starting contact form setup...');
    setupContactForm();
    
    ContactLogger.log('===== Contact Page Initialization Complete =====');
});

// Pre-fill email if user is authenticated
function prefillUserEmail() {
    ContactLogger.log('Checking if user is authenticated for email pre-fill');
    
    try {
        // Check if ResumeAnalyzer exists
        if (!window.ResumeAnalyzer) {
            ContactLogger.warn('ResumeAnalyzer object not found on window - user authentication check skipped');
            return;
        }
        
        ContactLogger.log('ResumeAnalyzer found, checking authentication status');
        
        // Check if user is authenticated
        if (!window.ResumeAnalyzer.isUserAuthenticated()) {
            ContactLogger.log('User is not authenticated - skipping pre-fill');
            return;
        }
        
        ContactLogger.log('User is authenticated, retrieving user data');
        const currentUser = window.ResumeAnalyzer.getCurrentUser();
        
        if (!currentUser) {
            ContactLogger.warn('User is authenticated but getCurrentUser() returned null/undefined');
            return;
        }
        
        ContactLogger.info('Current user data retrieved', { 
            hasEmail: !!currentUser.email, 
            hasName: !!currentUser.name 
        });
        
        // Pre-fill email
        if (currentUser.email) {
            const emailField = document.getElementById('email');
            if (emailField) {
                emailField.value = currentUser.email;
                ContactLogger.log(`Email field pre-filled with: ${currentUser.email}`);
            } else {
                ContactLogger.warn('Email field (#email) not found in DOM');
            }
        } else {
            ContactLogger.warn('User email not available in user object');
        }
        
        // Pre-fill name
        if (currentUser.name) {
            const nameField = document.getElementById('name');
            if (nameField) {
                nameField.value = currentUser.name;
                ContactLogger.log(`Name field pre-filled with: ${currentUser.name}`);
            } else {
                ContactLogger.warn('Name field (#name) not found in DOM');
            }
        } else {
            ContactLogger.warn('User name not available in user object');
        }
        
        ContactLogger.log('User email pre-fill process completed successfully');
        
    } catch (error) {
        ContactLogger.error('Error during user email pre-fill', error);
    }
}

// Setup contact form
function setupContactForm() {
    ContactLogger.log('Setting up contact form event handlers');
    
    const form = document.getElementById('contactForm');
    const submitBtn = document.getElementById('submitBtn');
    const messagesContainer = document.getElementById('messagesContainer');

    // Validate required elements
    if (!form) {
        ContactLogger.error('Contact form element (#contactForm) not found - aborting setup');
        return;
    }
    ContactLogger.log('Contact form element found');
    
    if (!submitBtn) {
        ContactLogger.error('Submit button element (#submitBtn) not found - aborting setup');
        return;
    }
    ContactLogger.log('Submit button element found');
    
    if (!messagesContainer) {
        ContactLogger.warn('Messages container (#messagesContainer) not found - messages may not display');
    } else {
        ContactLogger.log('Messages container element found');
    }

    // Setup form submission handler
    form.addEventListener('submit', async function(e) {
        ContactLogger.log('===== Form Submission Started =====');
        e.preventDefault();
        ContactLogger.log('Default form submission prevented');
        
        // Validate form
        ContactLogger.log('Checking form validity');
        if (!form.checkValidity()) {
            ContactLogger.warn('Form validation failed - marking invalid fields');
            form.classList.add('was-validated');
            return false;
        }
        ContactLogger.log('Form validation passed');

        // Get form data
        ContactLogger.log('Collecting form data');
        const formData = {
            name: document.getElementById('name').value.trim(),
            email: document.getElementById('email').value.trim(),
            subject: document.getElementById('subject').value.trim(),
            category: document.getElementById('category').value,
            message: document.getElementById('message').value.trim()
        };
        
        ContactLogger.info('Form data collected', {
            name: formData.name,
            email: formData.email,
            subject: formData.subject,
            category: formData.category,
            messageLength: formData.message.length
        });

        // Validate email format
        ContactLogger.log('Validating email format');
        if (!isValidEmail(formData.email)) {
            ContactLogger.warn(`Email validation failed for: ${formData.email}`);
            showMessage('Please enter a valid email address.', 'danger');
            return false;
        }
        ContactLogger.log('Email format validation passed');

        // Validate message length
        ContactLogger.log(`Checking message length: ${formData.message.length} characters`);
        if (formData.message.length < 10) {
            ContactLogger.warn(`Message too short: ${formData.message.length} characters (minimum 10 required)`);
            showMessage('Please provide a more detailed message (at least 10 characters).', 'danger');
            return false;
        }
        ContactLogger.log('Message length validation passed');

        // Show loading state
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
        submitBtn.disabled = true;
        ContactLogger.log('Submit button disabled and loading state set');

        try {
            // Call API
            const apiUrl = 'https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/submit-contact';
            ContactLogger.log(`Sending POST request to API: ${apiUrl}`);
            ContactLogger.info('Request payload', formData);
            
            const startTime = performance.now();
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const endTime = performance.now();
            const requestDuration = Math.round(endTime - startTime);
            
            ContactLogger.log(`API response received in ${requestDuration}ms`);
            ContactLogger.info('Response status', {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok
            });

            const data = await response.json();
            ContactLogger.info('API response data parsed', data);

            if (response.ok && data.success) {
                // Show success message
                ContactLogger.log('Form submission successful');
                const successMessage = data.message || 'Thank you for contacting us! We\'ll get back to you soon.';
                showMessage(successMessage, 'success');
                ContactLogger.log(`Success message displayed: ${successMessage}`);
                
                // Reset form
                ContactLogger.log('Resetting form fields');
                form.reset();
                form.classList.remove('was-validated');
                ContactLogger.log('Form reset complete');
                
                // Scroll to top to show message
                ContactLogger.log('Scrolling to top of page to display message');
                window.scrollTo({ top: 0, behavior: 'smooth' });
            } else {
                // Show error message
                ContactLogger.error('Form submission failed', {
                    status: response.status,
                    data: data
                });
                const errorMessage = data.error || 'Failed to send message. Please try again.';
                showMessage(errorMessage, 'danger');
                ContactLogger.log(`Error message displayed: ${errorMessage}`);
            }
        } catch (error) {
            ContactLogger.error('Exception occurred during form submission', error);
            ContactLogger.error('Error details', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            showMessage('An error occurred. Please try again later.', 'danger');
        } finally {
            // Restore button
            ContactLogger.log('Restoring submit button to original state');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            ContactLogger.log('===== Form Submission Complete =====');
        }

        return false;
    });
    
    ContactLogger.log('Form submit event handler attached');

    // Add real-time validation
    ContactLogger.log('Setting up real-time field validation');
    const inputs = form.querySelectorAll('input, textarea, select');
    ContactLogger.log(`Found ${inputs.length} form inputs for validation`);
    
    inputs.forEach((input, index) => {
        const inputId = input.id || `input-${index}`;
        ContactLogger.log(`Attaching validation listeners to: ${inputId} (${input.tagName})`);
        
        input.addEventListener('blur', function() {
            ContactLogger.log(`Blur event on ${inputId}, value length: ${this.value.trim().length}`);
            if (this.value.trim() && this.checkValidity()) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
                ContactLogger.log(`${inputId} marked as valid`);
            } else if (this.value.trim()) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
                ContactLogger.warn(`${inputId} marked as invalid`);
            }
        });

        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid') || this.classList.contains('is-valid')) {
                ContactLogger.log(`Input event on ${inputId}, re-validating`);
                if (this.checkValidity()) {
                    this.classList.add('is-valid');
                    this.classList.remove('is-invalid');
                    ContactLogger.log(`${inputId} re-validated as valid`);
                } else {
                    this.classList.add('is-invalid');
                    this.classList.remove('is-valid');
                    ContactLogger.log(`${inputId} re-validated as invalid`);
                }
            }
        });
    });
    
    ContactLogger.log('Real-time validation setup complete');
    ContactLogger.log('Contact form setup finished successfully');
}

// Validate email format
function isValidEmail(email) {
    ContactLogger.log(`Validating email format: ${email}`);
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(email);
    ContactLogger.log(`Email validation result for ${email}: ${isValid}`);
    return isValid;
}

// Show message to user
function showMessage(message, type) {
    ContactLogger.log(`Displaying message - Type: ${type}, Message: ${message}`);
    
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) {
        ContactLogger.error('Messages container not found - cannot display message');
        return;
    }

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Clear previous messages
    const previousMessages = messagesContainer.children.length;
    ContactLogger.log(`Clearing ${previousMessages} previous messages`);
    messagesContainer.innerHTML = '';
    messagesContainer.appendChild(alertDiv);
    ContactLogger.log('New message alert added to DOM');

    // Auto-dismiss after 5 seconds
    ContactLogger.log('Setting auto-dismiss timer for 5 seconds');
    setTimeout(() => {
        ContactLogger.log('Auto-dismissing message alert');
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
            ContactLogger.log('Message alert removed from DOM');
        }, 150);
    }, 5000);
}