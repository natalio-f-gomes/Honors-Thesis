
console.log('=== PARSED-RESUME.JS LOADED ===');
//thorough logging added by copilot

// Add after displayStats function
async function findJobs() {
    console.group(' FIND JOBS FUNCTION');
    console.log('Function called at:', new Date().toISOString());
    
    const metadata = window.currentResumeMetadata;
    console.log('Current resume metadata:', metadata);
    
    if (!metadata) {
        console.error(' No metadata found');
        alert('Resume data not loaded');
        console.groupEnd();
        return;
    }
    
    const findJobsBtn = document.querySelector('.btn-primary');
    console.log('Find Jobs button element:', findJobsBtn);
    
    // Check if jobs already exist
    console.log('Checking jobs_s3_path:', metadata.jobs_s3_path);
    if (metadata.jobs_s3_path) {
        console.log(' Jobs already exist, redirecting without alert');
        const redirectUrl = `jobs.html?resumeId=${metadata.resume_id}`;
        console.log('Redirect URL:', redirectUrl);
        window.location.href = redirectUrl;
        console.groupEnd();
        return;
    }
    
    // No jobs yet, fetch them
    console.log(' No jobs found, starting fetch process');
    findJobsBtn.disabled = true;
    findJobsBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Finding Jobs...';
    console.log('Button state updated - disabled and showing spinner');
    
    try {
        const token = localStorage.getItem('idToken');
        console.log('Token retrieved:', token ? `${token.substring(0, 20)}...` : 'NULL');
        
        const requestBody = {
            resumeId: metadata.resume_id,
            careerField: metadata.career_field,
            experienceLevel: metadata.experience_level,
            location: metadata.preferred_location,
            resumeNumber: metadata.resume_number
        };
        console.log('Request body:', requestBody);
        
        const apiUrl = 'https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/get-jobs';
        console.log('API endpoint:', apiUrl);
        
        console.log(' Sending POST request...');
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(' Response not OK. Error text:', errorText);
            throw new Error('Failed to fetch jobs');
        }
        
        const data = await response.json();
        console.log(' Response data:', data);
        
        if (data.success) {
            console.log(' Success flag true, redirecting');
            const redirectUrl = `jobs.html?resumeId=${metadata.resume_id}`;
            console.log('Final redirect URL:', redirectUrl);
            window.location.href = redirectUrl;
        } else {
            console.warn(' Success flag false or missing');
        }
        
    } catch (error) {
        console.error(' ERROR IN FIND JOBS:', error);
        console.error('Error stack:', error.stack);
        alert('Failed to find jobs: ' + error.message);
    } finally {
        console.log(' Finally block - resetting button');
        findJobsBtn.disabled = false;
        findJobsBtn.innerHTML = '<i class="fas fa-briefcase me-2"></i>Find Jobs';
        console.groupEnd();
    }
}

document.addEventListener('DOMContentLoaded', async function() {
    console.group(' DOM CONTENT LOADED - PARSED RESUME PAGE');
    console.log('Timestamp:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    
    // Check authentication
    console.log('Checking authentication...');
    console.log('CognitoAuth exists:', !!window.CognitoAuth);
    
    if (!window.CognitoAuth || !window.CognitoAuth.isAuthenticated()) {
        console.error(' Not authenticated, redirecting to login');
        window.location.href = 'index.html?message=Please log in to view resume details';
        console.groupEnd();
        return;
    }
    console.log(' User is authenticated');

    // Get resume ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const resumeId = urlParams.get('id');
    console.log('Resume ID from URL:', resumeId);

    if (!resumeId) {
        console.error(' No resume ID provided in URL');
        showError('No resume ID provided');
        console.groupEnd();
        return;
    }

    // Load resume data
    console.log(' Loading resume data...');
    await loadResumeData(resumeId);
    console.groupEnd();
});

async function loadResumeData(resumeId) {
    console.group(' LOAD RESUME DATA');
    console.log('Resume ID:', resumeId);
    
    try {
        const token = localStorage.getItem('idToken');
        console.log('Token retrieved:', token ? `${token.substring(0, 20)}...` : 'NULL');
        
        const user = window.CognitoAuth.getCurrentUser();
        console.log('Current user:', user);
        
        if (!user) {
            throw new Error('User not found');
        }

        // Get resume metadata from DynamoDB via Lambda
        const metadataUrl = `https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/get-resume?resumeId=${resumeId}`;
        console.log(' Fetching metadata from:', metadataUrl);
        
        const metadataResponse = await fetch(metadataUrl, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        console.log('Metadata response status:', metadataResponse.status);
        console.log('Metadata response ok:', metadataResponse.ok);
        
        if (!metadataResponse.ok) {
            const errorText = await metadataResponse.text();
            console.error(' Metadata fetch failed:', errorText);
            throw new Error('Failed to load resume metadata');
        }

        const metadata = await metadataResponse.json();
        console.log(' Resume metadata received:', metadata);

        // Check if JSON analysis exists
        console.log('Checking JSON analysis...');
        console.log('json_s3_path:', metadata.json_s3_path);
        console.log('status:', metadata.status);
        
        if (!metadata.json_s3_path || metadata.status !== 'completed') {
            console.error(' Resume analysis not completed');
            showError('Resume analysis not completed yet. Please try again later.');
            console.groupEnd();
            return;
        }
        console.log(' Resume analysis is completed');

        // Get parsed JSON from S3 via Lambda
        const jsonUrl = `https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/get-resume-json?resumeId=${resumeId}`;
        console.log(' Fetching parsed JSON from:', jsonUrl);
        
        const jsonResponse = await fetch(jsonUrl, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        console.log('JSON response status:', jsonResponse.status);
        console.log('JSON response ok:', jsonResponse.ok);
        
        if (!jsonResponse.ok) {
            const errorText = await jsonResponse.text();
            console.error(' JSON fetch failed:', errorText);
            throw new Error('Failed to load resume analysis');
        }

        const parsedResume = await jsonResponse.json();
        console.log(' Parsed resume received:', parsedResume);

        // Display the resume
        console.log(' Displaying resume...');
        displayResume(parsedResume, metadata);
        console.log(' Resume displayed successfully');

    } catch (error) {
        console.error(' ERROR IN LOAD RESUME DATA:', error);
        console.error('Error stack:', error.stack);
        showError(error.message);
    } finally {
        console.groupEnd();
    }
}

function displayResume(parsed, metadata) {
    console.group(' DISPLAY RESUME');
    console.log('Parsed data:', parsed);
    console.log('Metadata:', metadata);
    
    // Store metadata globally for findJobs function
    window.currentResumeMetadata = metadata;
    console.log(' Metadata stored in window.currentResumeMetadata');

    // Hide loading, show content
    const loadingState = document.getElementById('loadingState');
    const resumeContent = document.getElementById('resumeContent');
    console.log('Loading state element:', loadingState);
    console.log('Resume content element:', resumeContent);
    
    loadingState.style.display = 'none';
    resumeContent.style.display = 'block';
    console.log(' Visibility toggled');

    // Update header
    const resumeNameElement = document.getElementById('resumeName');
    const resumeName = parsed.name || 'Professional Resume';
    resumeNameElement.textContent = resumeName;
    console.log('Resume name set to:', resumeName);

    // Personal Information
    console.log(' Displaying personal info...');
    displayPersonalInfo(parsed, metadata);

    // Skills
    console.log(' Displaying skills...');
    displaySkills(parsed.skills || []);

    // Education
    console.log(' Displaying education...');
    displayEducation(parsed.education || []);

    // Experience
    console.log(' Displaying experience...');
    displayExperience(parsed.experience || []);

    // Projects
    console.log(' Displaying projects...');
    displayProjects(parsed.projects || []);

    // Statistics
    console.log(' Displaying stats...');
    displayStats(parsed);

    console.log(' All sections displayed');
    console.groupEnd();
}

function displayPersonalInfo(parsed, metadata) {
    console.log('displayPersonalInfo called with:', { parsed, metadata });
    
    const personalInfoDiv = document.getElementById('personalInfo');
    console.log('Personal info div:', personalInfoDiv);
    
    // Career field mapping
    const careerFieldMap = {
        'software_engineering': 'Software Engineering',
        'data_science': 'Data Science',
        'web_development': 'Web Development',
        'accounting': 'Accounting',
        'agriculture': 'Agriculture',
        'android_development': 'Android Development'
    };

    const experienceLevelMap = {
        'entry': 'Entry Level (0-2 years)',
        'mid': 'Mid Level (3-5 years)',
        'senior': 'Senior Level (6-10 years)',
        'lead': 'Lead/Principal (10+ years)'
    };

    console.log('Career field:', metadata.career_field, '→', careerFieldMap[metadata.career_field]);
    console.log('Experience level:', metadata.experience_level, '→', experienceLevelMap[metadata.experience_level]);

    personalInfoDiv.innerHTML = `
        <div class="row">
            <div class="col-md-6 mb-3">
                <strong class="text-primary">Name:</strong>
                <div class="mt-1">${parsed.name || 'Not specified'}</div>
            </div>
            <div class="col-md-6 mb-3">
                <strong class="text-primary">Email:</strong>
                <div class="mt-1">
                    ${parsed.email ? `<a href="mailto:${parsed.email}" class="text-decoration-none">${parsed.email}</a>` : '<span class="text-muted">Not specified</span>'}
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <strong class="text-primary">Phone:</strong>
                <div class="mt-1">
                    ${parsed.phone ? `<a href="tel:${parsed.phone}" class="text-decoration-none">${parsed.phone}</a>` : '<span class="text-muted">Not specified</span>'}
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <strong class="text-primary">Location:</strong>
                <div class="mt-1">${parsed.location || 'Not specified'}</div>
            </div>
            <div class="col-md-6 mb-3">
                <strong class="text-primary">Career Field:</strong>
                <div class="mt-1"><strong>${careerFieldMap[metadata.career_field] || metadata.career_field || 'Not specified'}</strong></div>
            </div>
            <div class="col-md-6 mb-3">
                <strong class="text-primary">Experience Level:</strong>
                <div class="mt-1">${experienceLevelMap[metadata.experience_level] || metadata.experience_level || 'Not specified'}</div>
            </div>
        </div>
    `;
    console.log(' Personal info HTML set');
}

function displaySkills(skills) {
    console.log('displaySkills called with:', skills, 'Length:', skills.length);
    
    const skillsDiv = document.getElementById('skillsSection');
    
    if (skills && skills.length > 0) {
        const skillBadges = skills.map(skill => 
            `<span class="badge bg-primary px-3 py-2 me-2 mb-2">
                <i class="fas fa-check-circle me-1"></i>${skill}
            </span>`
        ).join('');
        
        skillsDiv.innerHTML = `<div class="d-flex flex-wrap">${skillBadges}</div>`;
        console.log(` Displayed ${skills.length} skills`);
    } else {
        skillsDiv.innerHTML = '<span class="text-muted">No skills specified</span>';
        console.log(' No skills to display');
    }
}

function displayEducation(education) {
    console.log('displayEducation called with:', education, 'Length:', education.length);
    
    const educationDiv = document.getElementById('educationSection');
    
    if (education && education.length > 0) {
        const educationHTML = education.map((edu, index) => `
            <div class="education-item mb-3 ${index < education.length - 1 ? 'border-bottom pb-3' : ''}">
                <div class="row">
                    <div class="col-md-8">
                        <h6 class="mb-1 text-dark">${edu.degree || 'Degree'} ${edu.field ? `in ${edu.field}` : ''}</h6>
                        <p class="mb-1 text-primary">${edu.school || 'Institution not specified'}</p>
                    </div>
                    <div class="col-md-4 text-md-end">
                        ${edu.graduation_year ? `
                            <span class="badge bg-success-subtle text-success px-3 py-2">
                                <i class="fas fa-calendar me-1"></i>${edu.graduation_year}
                            </span>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
        
        educationDiv.innerHTML = educationHTML;
        console.log(` Displayed ${education.length} education entries`);
    } else {
        educationDiv.innerHTML = '<span class="text-muted">No education information specified</span>';
        console.log(' No education to display');
    }
}

function displayExperience(experience) {
    console.log('displayExperience called with:', experience, 'Length:', experience.length);
    
    const experienceDiv = document.getElementById('experienceSection');
    
    if (experience && experience.length > 0) {
        const experienceHTML = experience.map((exp, index) => `
            <div class="experience-item mb-4 ${index < experience.length - 1 ? 'border-bottom pb-4' : ''}">
                <div class="row">
                    <div class="col-md-8">
                        <h6 class="mb-1 text-dark">${exp.title || 'Position'}</h6>
                        <p class="mb-1 text-primary">${exp.company || 'Company'}</p>
                        ${exp.location ? `
                            <p class="mb-2 text-muted small">
                                <i class="fas fa-map-marker-alt me-1"></i>${exp.location}
                            </p>
                        ` : ''}
                        ${exp.description ? `<p class="mb-0 text-dark">${exp.description}</p>` : ''}
                    </div>
                    <div class="col-md-4 text-md-end">
                        ${exp.start_date || exp.end_date ? `
                            <span class="badge bg-warning-subtle text-warning px-3 py-2">
                                <i class="fas fa-calendar me-1"></i>
                                ${exp.start_date || ''}${exp.start_date && exp.end_date ? ' - ' : ''}${exp.end_date || 'Present'}
                            </span>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
        
        experienceDiv.innerHTML = experienceHTML;
        console.log(` Displayed ${experience.length} experience entries`);
    } else {
        experienceDiv.innerHTML = '<span class="text-muted">No work experience specified</span>';
        console.log(' No experience to display');
    }
}

function displayProjects(projects) {
    console.log('displayProjects called with:', projects, 'Length:', projects.length);
    
    const projectsDiv = document.getElementById('projectsSection');
    const projectsCard = document.getElementById('projectsCard');
    
    if (projects && projects.length > 0) {
        const projectsHTML = projects.map((project, index) => `
            <div class="project-item mb-3 ${index < projects.length - 1 ? 'border-bottom pb-3' : ''}">
                <h6 class="mb-2 text-dark">${project.name || 'Project'}</h6>
                ${project.description ? `<p class="mb-2 text-dark">${project.description}</p>` : ''}
                ${project.technologies && project.technologies.length > 0 ? `
                    <div class="d-flex flex-wrap gap-1">
                        ${project.technologies.map(tech => 
                            `<span class="badge bg-info-subtle text-info px-2 py-1">${tech}</span>`
                        ).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        projectsDiv.innerHTML = projectsHTML;
        projectsCard.style.display = 'block';
        console.log(` Displayed ${projects.length} projects`);
    } else {
        projectsCard.style.display = 'none';
        console.log(' No projects to display, hiding card');
    }
}

function displayStats(parsed) {
    console.log('displayStats called with:', parsed);
    
    const statsDiv = document.getElementById('statsSection');
    
    const stats = [
        {
            icon: 'fa-code',
            color: 'primary',
            count: (parsed.skills || []).length,
            label: 'Skills Listed'
        },
        {
            icon: 'fa-briefcase',
            color: 'warning',
            count: (parsed.experience || []).length,
            label: 'Work Experiences'
        },
        {
            icon: 'fa-graduation-cap',
            color: 'success',
            count: (parsed.education || []).length,
            label: 'Education Entries'
        },
        {
            icon: 'fa-project-diagram',
            color: 'info',
            count: (parsed.projects || []).length,
            label: 'Projects'
        }
    ];

    console.log('Stats calculated:', stats);

    statsDiv.innerHTML = stats.map(stat => `
        <div class="col-lg-3 col-md-6 mb-3">
            <div class="p-3 bg-light rounded">
                <i class="fas ${stat.icon} fa-2x text-${stat.color} mb-2"></i>
                <h6 class="mb-0">${stat.count}</h6>
                <small class="text-muted">${stat.label}</small>
            </div>
        </div>
    `).join('');
    console.log(' Stats HTML set');
}

function showError(message) {
    console.error(' SHOWING ERROR:', message);
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('errorState').style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
}

console.log('=== PARSED-RESUME.JS FULLY LOADED ===');