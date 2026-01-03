// Feedback page specific JavaScript 


const COGNITO_AUTH_HEADER_PREFIX = ''; 


// Logger utility

const FeedbackLogger = {
  log(message, data = null) {
    const ts = new Date().toISOString();
    console.log(`[Feedback Form] ${ts} - ${message}`, data || '');
  },
  error(message, error = null) {
    const ts = new Date().toISOString();
    console.error(`[Feedback Form ERROR] ${ts} - ${message}`, error || '');
  },
  warn(message, data = null) {
    const ts = new Date().toISOString();
    console.warn(`[Feedback Form WARNING] ${ts} - ${message}`, data || '');
  },
  info(message, data = null) {
    const ts = new Date().toISOString();
    console.info(`[Feedback Form INFO] ${ts} - ${message}`, data || '');
  }
};

// Utility: showMessage fallback (optional messages container)
function showFeedbackMessage(message, type = 'info') {
  const container = document.getElementById('messagesContainer');
  if (!container) {
    FeedbackLogger.warn('messagesContainer not found; falling back to alert()');
    alert(message);
    return;
  }

  const icon = type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle';
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.setAttribute('role', 'alert');
  alertDiv.innerHTML = `
    <i class="fas fa-${icon} me-2"></i>${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;

  container.innerHTML = '';
  container.appendChild(alertDiv);

  setTimeout(() => {
    alertDiv.classList.remove('show');
    setTimeout(() => alertDiv.remove(), 150);
  }, 5000);
}

// Utility: robust token retrieval

async function getAuthTokenRobust() {
  try {
    // 1) Prefer ResumeAnalyzer helper if available
    if (window.ResumeAnalyzer && typeof window.ResumeAnalyzer.getIdToken === 'function') {
      const t = await window.ResumeAnalyzer.getIdToken();
      if (t) return t;
    }

    // 2) Try CognitoAuth session in multiple shapes
    if (window.CognitoAuth && typeof window.CognitoAuth.getSession === 'function') {
      const session = await window.CognitoAuth.getSession();
      if (session) {
        // shape A (amplify-like plain object)
        if (session.idToken && session.idToken.jwtToken) {
          return session.idToken.jwtToken;
        }
        // shape B (Amazon Cognito SDK)
        if (typeof session.getIdToken === 'function') {
          const idt = session.getIdToken();
          if (idt && typeof idt.getJwtToken === 'function') {
            return idt.getJwtToken();
          }
        }
      }
    }

    // 3) Fallback to localStorage (your other pages set this)
    const ls = localStorage.getItem('idToken');
    if (ls) return ls;

    return null;
  } catch (e) {
    FeedbackLogger.error('Token helper failed', e);
    return null;
  }
}

// UI toggling helpers

function toggleFeedbackLoginUI(showForm) {
  const feedbackFormContainer = document.getElementById('feedbackFormContainer');
  const loginPromptContainer = document.getElementById('loginPromptContainer');
  if (feedbackFormContainer) feedbackFormContainer.style.display = showForm ? 'block' : 'none';
  if (loginPromptContainer) loginPromptContainer.style.display = showForm ? 'none' : 'block';
}

function setCurrentYear() {
  try {
    const currentYear = new Date().getFullYear();
    const yearElement = document.getElementById('currentYear');
    if (yearElement) {
      yearElement.textContent = currentYear;
      FeedbackLogger.log(`Current year set to: ${currentYear}`);
    } else {
      FeedbackLogger.warn('Current year element (#currentYear) not found in DOM');
    }
  } catch (error) {
    FeedbackLogger.error('Error setting current year', error);
  }
}

// Auth status check (logs + toggle)

function checkAuthenticationStatus() {
  FeedbackLogger.log('Checking authentication status and toggling UI containers');
  try {
    const isAuth = !!(window.ResumeAnalyzer && typeof window.ResumeAnalyzer.isUserAuthenticated === 'function' && window.ResumeAnalyzer.isUserAuthenticated());
    FeedbackLogger.info('Authentication check result', {
      hasResumeAnalyzer: !!window.ResumeAnalyzer,
      isAuthenticated: isAuth
    });

    const feedbackFormContainer = document.getElementById('feedbackFormContainer');
    const loginPromptContainer = document.getElementById('loginPromptContainer');

    if (!feedbackFormContainer) FeedbackLogger.error('Feedback form container (#feedbackFormContainer) not found in DOM');
    if (!loginPromptContainer) FeedbackLogger.error('Login prompt container (#loginPromptContainer) not found in DOM');

    toggleFeedbackLoginUI(isAuth);
    FeedbackLogger.log('Authentication status check completed');
  } catch (error) {
    FeedbackLogger.error('Error during authentication status check', error);
  }
}


// Main form setup

function setupFeedbackForm() {
  FeedbackLogger.log('===== Starting Feedback Form Setup =====');

  try {
    const stars = document.querySelectorAll('.rating-stars i');
    const ratingInput = document.getElementById('rating');
    const submitBtn = document.getElementById('submitBtn');
    const ratingText = document.getElementById('rating-text');
    const form = document.getElementById('feedbackForm');

    FeedbackLogger.log(`Found ${stars.length} star elements`);
    if (!submitBtn) { FeedbackLogger.error('Submit button (#submitBtn) not found'); return; }
    if (!form) { FeedbackLogger.error('Feedback form (#feedbackForm) not found - aborting setup'); return; }
    if (!ratingInput) FeedbackLogger.error('Rating input (#rating) not found');

    let selectedRating = 0;
    const ratingTexts = {
      1: "Poor - We need to improve",
      2: "Fair - Below expectations",
      3: "Good - Meets expectations",
      4: "Very Good - Above expectations",
      5: "Excellent - Exceeds expectations"
    };

    function updateStars(rating) {
      FeedbackLogger.log(`Updating stars to rating: ${rating}`);
      selectedRating = parseInt(rating);

      stars.forEach(star => {
        const starRating = parseInt(star.getAttribute('data-rating'));
        if (starRating <= rating) {
          star.classList.remove('far');
          star.classList.add('fas', 'selected');
        } else {
          star.classList.remove('fas', 'selected');
          star.classList.add('far');
        }
        // reset hover styles
        star.style.transform = 'scale(1)';
        if (!star.classList.contains('selected')) {
          star.style.color = 'rgba(255, 193, 7, 0.5)';
        }
      });

      if (ratingInput) ratingInput.value = String(rating);
      if (ratingText) ratingText.textContent = ratingTexts[rating] || "Click on the stars to rate";
      checkFormValidity();
    }

    // Stars listeners
    stars.forEach((star, idx) => {
      star.addEventListener('click', function () {
        const rating = this.getAttribute('data-rating');
        updateStars(rating);
      });
      star.addEventListener('mouseenter', function () {
        const r = parseInt(this.getAttribute('data-rating'));
        stars.forEach(s => {
          const sr = parseInt(s.getAttribute('data-rating'));
          if (sr <= r) {
            s.style.color = '#ffc107';
            s.style.transform = 'scale(1.2)';
          }
        });
      });
      star.addEventListener('mouseleave', function () {
        stars.forEach(s => {
          s.style.transform = 'scale(1)';
          if (!s.classList.contains('selected')) {
            s.style.color = 'rgba(255, 193, 7, 0.5)';
          }
        });
      });
    });

    // Field listeners + validation
    const categoryElement = document.getElementById('category');
    const messageElement = document.getElementById('message');

    function checkFormValidity() {
      const category = categoryElement ? categoryElement.value : '';
      const message = messageElement ? messageElement.value.trim() : '';
      const rating = ratingInput ? parseInt(ratingInput.value || '0') : 0;

      const isValid = rating >= 1 && !!category && message.length >= 10;
      submitBtn.disabled = !isValid;
      submitBtn.style.background = isValid
        ? 'linear-gradient(135deg, #28a745, #20c997)'
        : 'linear-gradient(135deg, #6c757d, #495057)';
      FeedbackLogger.log(`Form validity: ${isValid}`, { rating, category, messageLen: message.length });

      if (!isValid) {
        if (rating < 1) FeedbackLogger.warn('Validation: Rating not selected');
        if (!category) FeedbackLogger.warn('Validation: Category not selected');
        if (message.length < 10) FeedbackLogger.warn(`Validation: Message too short (${message.length})`);
      }
      return isValid;
    }

    if (categoryElement) {
      categoryElement.addEventListener('change', checkFormValidity);
    } else {
      FeedbackLogger.error('Category element (#category) not found');
    }

    if (messageElement) {
      messageElement.addEventListener('input', checkFormValidity);
    } else {
      FeedbackLogger.error('Message element (#message) not found');
    }

    // Submit handler
    form.addEventListener('submit', async function (e) {
      FeedbackLogger.log('===== Feedback Form Submission Started =====');
      e.preventDefault();

      if (!checkFormValidity()) {
        FeedbackLogger.warn('Submission blocked: form invalid');
        showFeedbackMessage('Please complete all required fields.', 'danger');
        return false;
      }

      // Loading state
      const originalHTML = submitBtn.innerHTML;
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Submitting...';
      submitBtn.disabled = true;

      // Compose payload
      const payload = {
        rating: selectedRating || parseInt(ratingInput?.value || '0'),
        category: categoryElement ? categoryElement.value : '',
        message: messageElement ? messageElement.value.trim() : ''
      };
      FeedbackLogger.info('Submitting payload', payload);

      try {
        // Acquire token
        let token = await getAuthTokenRobust();
        if (!token) {
          FeedbackLogger.error('Unable to retrieve authentication token');
          showFeedbackMessage('Your session expired. Please sign in again.', 'danger');
          toggleFeedbackLoginUI(false);
          return false;
        }

        // Call API
        const apiUrl = 'https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/submit-feedback';
        FeedbackLogger.log(`POST ${apiUrl}`);

        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': COGNITO_AUTH_HEADER_PREFIX + token
          },
          body: JSON.stringify(payload)
        });

        let data = null;
        try {
          data = await response.json();
        } catch (_e) {
          FeedbackLogger.warn('Response was not valid JSON');
        }
        FeedbackLogger.info('API response', { status: response.status, ok: response.ok, data });

        if (response.ok && data && data.success) {
          FeedbackLogger.log('Feedback submitted successfully');
          if (window.ResumeAnalyzer && typeof window.ResumeAnalyzer.displayMessage === 'function') {
            window.ResumeAnalyzer.displayMessage(data.message || 'Thank you for your feedback!', 'success');
          } else {
            showFeedbackMessage(data.message || 'Thank you for your feedback!', 'success');
          }

          // Reset form + stars
          form.reset();
          if (ratingInput) ratingInput.value = '0';
          selectedRating = 0;
          stars.forEach(star => {
            star.classList.remove('fas', 'selected');
            star.classList.add('far');
            star.style.transform = 'scale(1)';
            star.style.color = 'rgba(255, 193, 7, 0.5)';
          });
          if (ratingText) ratingText.textContent = 'Click on the stars to rate';
          window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
          const errMsg = (data && (data.error || data.message)) || 'Failed to submit feedback. Please try again.';
          FeedbackLogger.error('Feedback submission failed', data || {});
          if (window.ResumeAnalyzer && typeof window.ResumeAnalyzer.displayMessage === 'function') {
            window.ResumeAnalyzer.displayMessage(errMsg, 'danger');
          } else {
            showFeedbackMessage(errMsg, 'danger');
          }
        }
      } catch (error) {
        FeedbackLogger.error('Error submitting feedback', error);
        if (window.ResumeAnalyzer && typeof window.ResumeAnalyzer.displayMessage === 'function') {
          window.ResumeAnalyzer.displayMessage('An error occurred. Please try again later.', 'danger');
        } else {
          showFeedbackMessage('An error occurred. Please try again later.', 'danger');
        }
      } finally {
        submitBtn.innerHTML = originalHTML;
        submitBtn.disabled = false;
        FeedbackLogger.log('===== Feedback Form Submission Complete =====');
      }

      return false;
    });

    FeedbackLogger.log('===== Feedback Form Setup Complete =====');
  } catch (error) {
    FeedbackLogger.error('Critical error during feedback form setup', error);
    FeedbackLogger.error('Error details', { name: error.name, message: error.message, stack: error.stack });
  }
}


// Bootstrap on DOMContentLoaded

document.addEventListener('DOMContentLoaded', async function () {
  FeedbackLogger.log('===== Feedback Page Initialization Started =====');
  setCurrentYear();

  // Wait for auth objects to be ready (up to ~2s)
  FeedbackLogger.log('Waiting for ResumeAnalyzer/CognitoAuth readiness...');
  for (let i = 0; i < 20; i++) {
    if (window.ResumeAnalyzer && typeof window.ResumeAnalyzer.isUserAuthenticated === 'function') break;
    await new Promise(r => setTimeout(r, 100));
  }

  // Toggle UI based on current auth state
  checkAuthenticationStatus();

  try {
    const isAuth = !!(window.ResumeAnalyzer && typeof window.ResumeAnalyzer.isUserAuthenticated === 'function' && window.ResumeAnalyzer.isUserAuthenticated());
    if (!isAuth) {
      FeedbackLogger.warn('User not authenticated; showing login prompt');
      toggleFeedbackLoginUI(false);
      FeedbackLogger.log('===== Feedback Page Initialization Complete (unauthenticated) =====');
      return;
    }

    // Ensure we can actually fetch a token before enabling the form
    const token = await getAuthTokenRobust();
    if (!token) {
      FeedbackLogger.warn('Authenticated but missing token; showing login prompt and aborting form setup');
      toggleFeedbackLoginUI(false);
      showFeedbackMessage('Your session expired. Please sign in again.', 'danger');
      FeedbackLogger.log('===== Feedback Page Initialization Complete (token missing) =====');
      return;
    }

    // Token OK — show form and set up
    toggleFeedbackLoginUI(true);
    setupFeedbackForm();
  } catch (e) {
    FeedbackLogger.error('Initialization error', e);
  }

  FeedbackLogger.log('===== Feedback Page Initialization Complete =====');
});
