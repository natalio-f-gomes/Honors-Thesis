


console.log('=== UPLOAD.JS LOADED ===');
// Update profile function - redirects to Cognito hosted UI
function updateProfile() {
    // Get current session
    if (window.CognitoAuth) {
        // Cognito doesn't have a direct "update profile" page in hosted UI
        // So we'll create a simple prompt modal
        const name = prompt('Enter your new name:', document.getElementById('userName').textContent);
        
        if (name && name.trim()) {
            updateUserName(name.trim());
        }
    } else {
        alert('Authentication system not available');
    }
}

// Update user name via Cognito
async function updateUserName(newName) {
    try {
        const session = await window.CognitoAuth.getSession();
        
        if (!session) {
            alert('Not authenticated');
            return;
        }
        
        // Call Lambda to update Cognito user attributes
        const token = session.idToken.jwtToken;
        
        const response = await fetch('https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/update-profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                name: newName
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            alert('Profile updated successfully!');
            // Refresh the page to show new name
            location.reload();
        } else {
            alert('Failed to update profile: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        alert('Error updating profile. Please try again.');
    }
}

document.addEventListener('DOMContentLoaded', async function() {
    console.group(' DOM CONTENT LOADED - UPLOAD PAGE');
    console.log('Timestamp:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    
    const currentYear = new Date().getFullYear();
    document.getElementById('currentYear').textContent = currentYear;
    console.log(' Current year set to:', currentYear);
    
    console.log(' Checking authentication...');
    const isAuth = await checkAuthenticationAndRedirect();
    console.log('Authentication result:', isAuth);
    
    if (isAuth) {
        console.log(' User authenticated, proceeding with setup');
        console.log(' Checking resume limit...');
        await checkResumeLimit();
        console.log(' Initializing upload functionality...');
        initializeUpload();
    } else {
        console.log(' User not authenticated, redirected');
    }
    
    console.groupEnd();
});

// Check authentication
async function checkAuthenticationAndRedirect() {
    console.group(' CHECK AUTHENTICATION');
    console.log('ResumeAnalyzer exists:', !!window.ResumeAnalyzer);
    
    const isAuth = window.ResumeAnalyzer && window.ResumeAnalyzer.isUserAuthenticated();
    console.log('Is authenticated:', isAuth);
    
    if (!isAuth) {
        const redirectUrl = 'index.html?message=' + encodeURIComponent('Please login to upload your resume');
        console.log(' Not authenticated, redirecting to:', redirectUrl);
        window.location.href = redirectUrl;
        console.groupEnd();
        return false;
    }
    
    console.log('User is authenticated');
    console.groupEnd();
    return true;
}

// Check if user has reached resume limit
async function checkResumeLimit() {
    console.group(' CHECK RESUME LIMIT');
    
    try {
        const token = localStorage.getItem('idToken');
        console.log('Token retrieved:', token ? `${token.substring(0, 20)}...` : 'NULL');
        
        if (!token) {
            throw new Error('Not authenticated');
        }
        
        const apiUrl = 'https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/get-user-resumes';
        console.log(' API endpoint:', apiUrl);
        console.log(' Sending GET request...');
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(' Response not OK:', errorText);
            throw new Error('Failed to check resume limit');
        }
        
        const data = await response.json();
        console.log(' Response data:', data);
        
        const resumeCount = data.resumes ? data.resumes.length : 0;
        console.log('Resume count:', resumeCount);
        
        if (resumeCount >= 5) {
            console.warn(' Resume limit reached!');
            showLimitReachedMessage();
            console.groupEnd();
            return false;
        }
        
        console.log(' Resume limit not reached, can upload');
        console.groupEnd();
        return true;
        
    } catch (error) {
        console.error(' ERROR IN CHECK RESUME LIMIT:', error);
        console.error('Error stack:', error.stack);
        console.log('Continuing anyway (fail-safe)');
        console.groupEnd();
        return true;
    }
}

// Show limit reached message
function showLimitReachedMessage() {
    console.log(' Showing limit reached message');
    
    const container = document.querySelector('.container.py-5');
    console.log('Container element:', container);
    
    container.innerHTML = `
        <div class="row justify-content-center">
            <div class="col-lg-6">
                <div class="card border-0 shadow-lg" style="border-radius: 20px;">
                    <div class="card-body p-5 text-center">
                        <div class="alert-icon mb-4" style="width: 80px; height: 80px; background: linear-gradient(135deg, #dc3545, #c82333); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                            <i class="fas fa-exclamation-triangle fa-2x text-white"></i>
                        </div>
                        <h4 class="text-danger mb-3">Upload Limit Reached</h4>
                        <p class="text-muted mb-4">You have reached the maximum limit of 5 resumes. Please manage your existing resumes from your account page.</p>
                        <a href="account.html" class="btn btn-primary btn-lg" style="border-radius: 50px;">
                            <i class="fas fa-arrow-left me-2"></i>Go to My Resumes
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
    console.log(' Limit message displayed');
}

// Initialize upload functionality
function initializeUpload() {
    console.group(' INITIALIZE UPLOAD');
    console.log('Setting up upload form and event listeners');
    
    const fileInput = document.getElementById('fileInput');
    const careerField = document.getElementById('career_field');
    const experienceLevel = document.getElementById('experience_level');
    const preferredLocation = document.getElementById('preferred_location');
    const fileUploadArea = document.getElementById('fileUploadArea');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileType = document.getElementById('fileType');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadForm = document.getElementById('uploadForm');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const uploadTitle = document.getElementById('uploadTitle');
    const uploadDescription = document.getElementById('uploadDescription');
    const uploadIcon = document.getElementById('uploadIcon');

    console.log('All form elements:', {
        fileInput: !!fileInput,
        careerField: !!careerField,
        experienceLevel: !!experienceLevel,
        preferredLocation: !!preferredLocation,
        fileUploadArea: !!fileUploadArea,
        uploadBtn: !!uploadBtn,
        uploadForm: !!uploadForm
    });

    let droppedFile = null;
    console.log('DroppedFile initialized to null');

    // Event listeners
    console.log(' Attaching event listeners...');
    fileInput.addEventListener('change', handleFileSelect);
    fileUploadArea.addEventListener('dragover', handleDragOver);
    fileUploadArea.addEventListener('dragleave', handleDragLeave);
    fileUploadArea.addEventListener('drop', handleFileDrop);
    fileUploadArea.addEventListener('click', function(e) {
        if (!e.target.closest('.btn-outline-danger')) {
            console.log(' Upload area clicked, triggering file input');
            fileInput.click();
        }
    });
    console.log(' Event listeners attached');

    function handleFileSelect(e) {
        console.group(' FILE SELECT');
        console.log('Event:', e);
        const file = e.target.files[0];
        console.log('Selected file:', file);
        console.log('File details:', file ? {
            name: file.name,
            size: file.size,
            type: file.type
        } : 'No file');
        
        droppedFile = null;
        console.log('Cleared droppedFile');
        
        if (file && validateFile(file)) {
            console.log(' File valid, displaying info');
            displayFileInfo(file);
        } else {
            console.log(' File invalid or missing, clearing input');
            fileInput.value = '';
        }
        console.groupEnd();
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log(' Drag over');
        fileUploadArea.classList.add('drag-over');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log(' Drag leave');
        fileUploadArea.classList.remove('drag-over');
    }

    function handleFileDrop(e) {
        console.group(' FILE DROP');
        e.preventDefault();
        e.stopPropagation();
        fileUploadArea.classList.remove('drag-over');
        console.log('Drop event:', e);

        const files = e.dataTransfer.files;
        console.log('Dropped files count:', files.length);
        
        if (files.length > 0) {
            const file = files[0];
            console.log('First file:', {
                name: file.name,
                size: file.size,
                type: file.type
            });
            
            if (validateFile(file)) {
                console.log(' File valid, setting as droppedFile');
                droppedFile = file;
                displayFileInfo(file);
                fileInput.value = '';
                console.log('Cleared file input');
            }
        }
        console.groupEnd();
    }

    function validateFile(file) {
        console.group(' VALIDATE FILE');
        console.log('File to validate:', {
            name: file.name,
            size: file.size,
            type: file.type
        });
        
        const fileName = file.name.toLowerCase();
        const fileType = file.type.toLowerCase();
        console.log('Lowercase name:', fileName);
        console.log('Lowercase type:', fileType);

        const isPDF = fileName.endsWith('.pdf') || fileType === 'application/pdf';
        console.log('Is PDF:', isPDF);

        if (!isPDF) {
            console.error(' Not a PDF file');
            alert('Please upload only PDF files.');
            console.groupEnd();
            return false;
        }

        const maxSize = 10 * 1024 * 1024;
        console.log('File size:', file.size, 'Max size:', maxSize);
        
        if (file.size > maxSize) {
            console.error(' File too large');
            alert('File size exceeds 10MB limit. Please choose a smaller file.');
            console.groupEnd();
            return false;
        }

        console.log(' File validation passed');
        console.groupEnd();
        return true;
    }

    function displayFileInfo(file) {
        console.group(' DISPLAY FILE INFO');
        console.log('File:', file.name);
        
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        fileType.textContent = 'PDF Document';
        console.log('Set file info display');

        fileInfo.style.display = 'block';
        uploadTitle.textContent = 'File Selected';
        uploadDescription.style.display = 'none';
        uploadIcon.className = 'fas fa-check-circle fa-2x text-white';
        console.log('Updated UI for file selected state');

        fileUploadArea.style.borderColor = '#28a745';
        fileUploadArea.style.background = 'linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(32, 201, 151, 0.1))';
        console.log('Applied success styling');

        checkFormValidity();
        console.groupEnd();
    }

    function removeFile() {
        console.group(' REMOVE FILE');
        console.log('Removing file');
        
        fileInput.value = '';
        droppedFile = null;
        fileInfo.style.display = 'none';
        uploadTitle.textContent = 'Drag & Drop Your Resume';
        uploadDescription.style.display = 'block';
        uploadIcon.className = 'fas fa-cloud-upload-alt fa-2x text-white';

        fileUploadArea.style.borderColor = '#e9ecef';
        fileUploadArea.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05))';
        console.log(' File removed and UI reset');

        checkFormValidity();
        console.groupEnd();
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        const result = parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        console.log(`Formatted ${bytes} bytes to ${result}`);
        return result;
    }

    uploadForm.addEventListener('submit', async function(e) {
        console.group(' FORM SUBMIT');
        e.preventDefault();
        console.log('Form submission prevented (will handle manually)');
        console.log('Timestamp:', new Date().toISOString());

        const file = droppedFile || (fileInput.files.length > 0 ? fileInput.files[0] : null);
        console.log('File to upload:', file ? file.name : 'NULL');

        if (!file || !validateFile(file)) {
            console.error(' No valid file to upload');
            console.groupEnd();
            return false;
        }

        console.log(' Reading file as base64...');
        const reader = new FileReader();
        
        reader.onload = async function(e) {
            console.group(' FILE READ COMPLETE');
            console.log('File read event:', e);
            
            const base64Data = e.target.result.split(',')[1];
            console.log('Base64 data length:', base64Data.length);
            console.log('Base64 preview:', base64Data.substring(0, 50) + '...');
            
            const requestBody = {
                file_data: base64Data,
                file_name: file.name,
                career_field: careerField.value,
                experience_level: experienceLevel.value,
                preferred_location: preferredLocation.value
            };
            console.log('Request body prepared:', {
                file_name: requestBody.file_name,
                career_field: requestBody.career_field,
                experience_level: requestBody.experience_level,
                preferred_location: requestBody.preferred_location,
                file_data_length: requestBody.file_data.length
            });
            
            uploadProgress.style.display = 'block';
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing Resume...';
            uploadBtn.disabled = true;
            console.log(' UI updated - showing progress');

            simulateProgress();
            console.log(' Progress simulation started');

            try {
                const token = localStorage.getItem('idToken');
                console.log('Token retrieved:', token ? `${token.substring(0, 20)}...` : 'NULL');

                if (!token) {
                    throw new Error('Not authenticated. Please log in.');
                }

                const API_ENDPOINT = 'https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/upload';
                console.log(' API endpoint:', API_ENDPOINT);
                console.log(' Sending POST request...');
                console.log('Request headers:', {
                    'Authorization': `Bearer ${token.substring(0, 20)}...`,
                    'Content-Type': 'application/json'
                });

                const response = await fetch(API_ENDPOINT, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody)
                });

                console.log('Response received');
                console.log('Response status:', response.status);
                console.log('Response ok:', response.ok);
                console.log('Response headers:', Object.fromEntries(response.headers.entries()));

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error(' Response not OK:', errorText);
                    throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
                }

                const data = await response.json();
                console.log(' Response data:', data);

                progressBar.style.width = '100%';
                progressText.textContent = 'Upload complete!';
                console.log(' Progress bar complete');

                setTimeout(() => {
                    console.log(' Redirecting to parsed resume page');
                    const redirectUrl = `parsed-resume.html?id=${data.data.resume_id}`;
                    console.log('Redirect URL:', redirectUrl);
                    window.location.href = redirectUrl;
                }, 1000);

            } catch (error) {
                console.error(' ERROR IN UPLOAD:', error);
                console.error('Error stack:', error.stack);
                
                progressBar.style.width = '100%';
                progressBar.classList.remove('bg-primary');
                progressBar.classList.add('bg-danger');
                progressText.textContent = 'Upload failed: ' + error.message;
                console.log(' Error displayed to user');

                uploadBtn.innerHTML = '<i class="fas fa-cloud-upload-alt me-2"></i>Upload Resume';
                uploadBtn.disabled = false;
                console.log(' Button reset');
            }
            
            console.groupEnd();
        };

        reader.onerror = function(error) {
            console.error(' FILE READ ERROR:', error);
        };

        reader.readAsDataURL(file);
        console.log(' Started reading file as data URL');
        console.groupEnd();
        return false;
    });

    function simulateProgress() {
        console.log(' Progress simulation started');
        let progress = 0;
        const interval = setInterval(function() {
            progress += Math.random() * 15;
            if (progress > 90) {
                progress = 90;
                clearInterval(interval);
                console.log(' Progress simulation capped at 90%');
            }

            progressBar.style.width = progress + '%';

            if (progress < 30) {
                progressText.textContent = 'Uploading file...';
            } else if (progress < 60) {
                progressText.textContent = 'Processing document...';
            } else if (progress < 90) {
                progressText.textContent = 'Analyzing content...';
            } else {
                progressText.textContent = 'Finalizing results...';
            }
        }, 200);
    }

    function checkFormValidity() {
        console.group(' CHECK FORM VALIDITY');
        
        const isFileSelected = droppedFile !== null || fileInput.files.length > 0;
        const isCareerFieldSelected = careerField.value !== '';
        const isExperienceLevelSelected = experienceLevel.value !== '';
        const isLocationFilled = preferredLocation.value.trim() !== '';

        console.log('Form validation:', {
            isFileSelected,
            isCareerFieldSelected,
            isExperienceLevelSelected,
            isLocationFilled
        });

        const isValid = isFileSelected && isCareerFieldSelected && isExperienceLevelSelected && isLocationFilled;
        console.log('Overall validity:', isValid);

        uploadBtn.disabled = !isValid;
        console.log('Upload button disabled:', uploadBtn.disabled);
        
        console.groupEnd();
    }

    careerField.addEventListener('change', checkFormValidity);
    experienceLevel.addEventListener('change', checkFormValidity);
    preferredLocation.addEventListener('input', checkFormValidity);
    console.log(' Form validation listeners attached');

    window.removeFile = removeFile;
    console.log(' removeFile function exposed globally');
    
    console.groupEnd();
}

console.log('=== UPLOAD.JS FULLY LOADED ===');