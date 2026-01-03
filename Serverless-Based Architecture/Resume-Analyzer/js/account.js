// Account page – Minimal: show email + resume history only (null-safe)
// ENHANCED: Now includes resume count display and upload button state

document.addEventListener('DOMContentLoaded', function () {
  const yearEl = document.getElementById('currentYear');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  checkAuthAndLoad();
  setupLoginButton();
});

function checkAuthAndLoad() {
  const isAuth = !!(window.ResumeAnalyzer && window.ResumeAnalyzer.isUserAuthenticated && window.ResumeAnalyzer.isUserAuthenticated());
  const authed = document.getElementById('authenticatedContent');
  const unauthed = document.getElementById('unauthenticatedContent');

  if (isAuth) {
    if (authed) authed.style.display = 'block';
    if (unauthed) unauthed.style.display = 'none';
    loadEmailOnly();
    loadResumeHistory();
  } else {
    if (authed) authed.style.display = 'none';
    if (unauthed) unauthed.style.display = 'block';
  }
}

function loadEmailOnly() {
  try {
    const emailEl = document.getElementById('userEmail');
    if (!emailEl) return; // element not on page, safely bail

    const user = (window.ResumeAnalyzer && typeof window.ResumeAnalyzer.getCurrentUser === 'function')
      ? window.ResumeAnalyzer.getCurrentUser()
      : null;

    emailEl.textContent = (user && user.email) ? user.email : 'Not provided';
  } catch (e) {
    console.error('Error loading email', e);
  }
}

async function loadResumeHistory() {
  const container = document.getElementById('resumeHistoryContainer');
  if (!container) return;

  container.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>
      <p class="text-muted mt-3">Loading your resumes...</p>
    </div>
  `;

  try {
    const token = localStorage.getItem('idToken');
    if (!token) throw new Error('Not authenticated');

    const resp = await fetch('https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/get-user-resumes', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!resp.ok) throw new Error(`API returned ${resp.status}`);
    const data = await resp.json();
    const resumes = Array.isArray(data.resumes) ? data.resumes : [];

    // Update resume count
    updateResumeCount(resumes.length);

    if (resumes.length) {
      displayResumes(resumes);
    } else {
      displayNoResumes();
    }
  } catch (err) {
    console.error('Error loading resumes:', err);
    container.innerHTML = `
      <div class="text-center py-5">
        <div class="alert alert-danger">
          <i class="fas fa-exclamation-circle me-2"></i>Error loading resumes: ${err.message}
        </div>
      </div>
    `;
    // Set count to 0 on error
    updateResumeCount(0);
  }
}

function updateResumeCount(count) {
  const countEl = document.getElementById('resumeCount');
  const uploadBtn = document.getElementById('uploadNewBtn');
  
  if (countEl) {
    countEl.textContent = count;
  }
  
  // Disable upload button and update styling if limit reached
  if (uploadBtn) {
    if (count >= 5) {
      uploadBtn.classList.remove('btn-success');
      uploadBtn.classList.add('btn-secondary');
      uploadBtn.style.cursor = 'not-allowed';
      uploadBtn.style.opacity = '0.6';
      uploadBtn.innerHTML = '<i class="fas fa-ban me-2"></i>Limit Reached';
      uploadBtn.onclick = function(e) {
        e.preventDefault();
        alert('You have reached the maximum limit of 5 resumes. Please delete an existing resume to upload a new one.');
        return false;
      };
    } else {
      uploadBtn.classList.remove('btn-secondary');
      uploadBtn.classList.add('btn-success');
      uploadBtn.style.cursor = 'pointer';
      uploadBtn.style.opacity = '1';
      uploadBtn.innerHTML = '<i class="fas fa-cloud-upload-alt me-2"></i>Upload New Resume';
      uploadBtn.onclick = null;
    }
  }
}

function displayResumes(resumes) {
  const container = document.getElementById('resumeHistoryContainer');
  if (!container) return;

  resumes.sort((a, b) => (a.resume_number || 0) - (b.resume_number || 0));

  let html = '<div class="row">';
  for (const resume of resumes) {
    const statusBadge = resume.status === 'completed'
      ? '<span class="badge bg-success-subtle text-success px-2 py-1"><i class="fas fa-check-circle me-1"></i>Completed</span>'
      : '<span class="badge bg-warning-subtle text-warning px-2 py-1"><i class="fas fa-hourglass-half me-1"></i>Processing</span>';

    html += `
      <div class="col-md-6 mb-3">
        <div class="resume-card p-3 border rounded-3 h-100" style="transition: all 0.3s ease; border: 2px solid #e9ecef !important;">
          <div class="d-flex align-items-start">
            <div class="resume-icon me-3" style="width: 50px; height: 50px; background: linear-gradient(135deg, #6f42c1, #8b5cf6); border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
              <span class="text-white fw-bold">#${resume.resume_number ?? '?'}</span>
            </div>
            <div class="resume-info flex-grow-1">
              <h6 class="mb-1">
                ${resume.status === 'completed'
                  ? `<a href="parsed-resume.html?id=${resume.resume_id}" class="text-decoration-none text-dark fw-bold">${formatCareerField(resume.career_field)} Resume</a>`
                  : `<span class="text-muted">${formatCareerField(resume.career_field)} Resume</span>`
                }
              </h6>
              <p class="text-muted small mb-2">
                <i class="fas fa-calendar-alt me-1"></i>
                Uploaded ${formatDate(resume.upload_date)}
              </p>
              <div class="d-flex gap-2 flex-wrap">
                ${statusBadge}
                <span class="badge bg-info-subtle text-info px-2 py-1">
                  <i class="fas fa-briefcase me-1"></i>${formatExperienceLevel(resume.experience_level)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>`;
  }
  html += '</div>';
  container.innerHTML = html;
}

function displayNoResumes() {
  const container = document.getElementById('resumeHistoryContainer');
  if (!container) return;

  container.innerHTML = `
    <div class="text-center py-5">
      <div class="empty-state-icon mb-4" style="width: 80px; height: 80px; background: linear-gradient(135deg, #6c757d, #495057); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
        <i class="fas fa-file-alt fa-2x text-white opacity-75"></i>
      </div>
      <h5 class="text-muted mb-3">No Resumes Yet</h5>
      <p class="text-muted mb-4">You haven't uploaded any resumes yet.</p>
      <a href="upload.html" class="btn btn-success px-4 py-2" style="border-radius: 50px;">
        <i class="fas fa-cloud-upload-alt me-2"></i>Upload Your First Resume
      </a>
    </div>
  `;
}

function formatCareerField(field) {
  if (!field) return 'General';
  return field.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}
function formatExperienceLevel(level) {
  const m = { entry: 'Entry', mid: 'Mid', senior: 'Senior', lead: 'Lead' };
  return m[level] || (level || 'N/A');
}
function formatDate(date) {
  const d = new Date(date);
  if (Number.isNaN(d.getTime())) return 'Unknown';
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function setupLoginButton() {
  const btn = document.getElementById('loginFromAccountBtn');
  if (!btn) return;
  btn.addEventListener('click', function () {
    if (window.CognitoAuth && typeof window.CognitoAuth.login === 'function') {
      window.CognitoAuth.login();
    } else {
      window.location.href = 'login.html';
    }
  });
}