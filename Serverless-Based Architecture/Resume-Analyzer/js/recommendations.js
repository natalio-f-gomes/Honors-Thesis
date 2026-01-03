
console.log('=== RECOMMENDATIONS.JS LOADED ===');

document.addEventListener('DOMContentLoaded', async function() {
    console.group(' DOM CONTENT LOADED - RECOMMENDATIONS PAGE');
    console.log('Timestamp:', new Date().toISOString());
    console.log('Current URL:', window.location.href);
    
    // Check auth
    console.log('Checking authentication...');
    console.log('CognitoAuth exists:', !!window.CognitoAuth);
    
    if (!window.CognitoAuth || !window.CognitoAuth.isAuthenticated()) {
        console.error(' Not authenticated, redirecting');
        window.location.href = 'index.html?message=Please log in';
        console.groupEnd();
        return;
    }
    console.log(' User is authenticated');

    const urlParams = new URLSearchParams(window.location.search);
    const resumeId = urlParams.get('resumeId');
    console.log('Resume ID from URL:', resumeId);

    if (!resumeId) {
        console.error(' No resume ID provided');
        showError('No resume ID provided');
        console.groupEnd();
        return;
    }

    // Set back button links
    const backToJobsBtn = document.getElementById('backToJobsBtn');
    const viewJobsBtn = document.getElementById('viewJobsBtn');
    const backUrl = `jobs.html?resumeId=${resumeId}`;
    
    console.log('Setting back button URLs to:', backUrl);
    backToJobsBtn.href = backUrl;
    viewJobsBtn.href = backUrl;
    console.log(' Back buttons configured');

    console.log(' Loading recommendations...');
    await loadRecommendations(resumeId);
    console.groupEnd();
});

async function loadRecommendations(resumeId) {
    console.group(' LOAD RECOMMENDATIONS');
    console.log('Resume ID:', resumeId);
    
    try {
        const token = localStorage.getItem('idToken');
        console.log('Token retrieved:', token ? `${token.substring(0, 20)}...` : 'NULL');
        
        const apiUrl = `https://abcafdfa.execute-api.us-east-1.amazonaws.com/prod/get-recommendations?resumeId=${resumeId}`;
        console.log(' API endpoint:', apiUrl);
        console.log('Sending GET request...');
        
        const response = await fetch(apiUrl, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
            const errorText = await response.text();
            console.error(' Response not OK. Error text:', errorText);
            throw new Error('Failed to load recommendations');
        }

        const data = await response.json();
        console.log(' Response data:', data);
        console.log('Data structure:', {
            success: data.success,
            hasRecommendations: !!data.recommendations,
            error: data.error
        });
        
        if (data.success && data.recommendations) {
            console.log(' Recommendations received, displaying...');
            console.log('Recommendations object keys:', Object.keys(data.recommendations));
            displayRecommendations(data.recommendations);
        } else if (data.error) {
            console.error(' API returned error:', data.error);
            showError(data.error);
        } else {
            console.warn(' Unexpected response format');
            showError('Unexpected response format');
        }

    } catch (error) {
        console.error(' ERROR IN LOAD RECOMMENDATIONS:', error);
        console.error('Error stack:', error.stack);
        showError(error.message);
    } finally {
        console.groupEnd();
    }
}

function displayRecommendations(recommendations) {
    console.group(' DISPLAY RECOMMENDATIONS');
    console.log('Recommendations data:', recommendations);
    console.log('Data structure:', {
        missing_technical_skills: recommendations.missing_technical_skills?.length || 0,
        missing_soft_skills: recommendations.missing_soft_skills?.length || 0,
        missing_education: recommendations.missing_education?.length || 0,
        missing_certifications: recommendations.missing_certifications?.length || 0,
        missing_experience: recommendations.missing_experience?.length || 0,
        priority_skills: recommendations.priority_skills?.length || 0,
        learning_resources: recommendations.learning_resources?.length || 0,
        recommended_actions: recommendations.recommended_actions?.length || 0
    });
    
    const loadingState = document.getElementById('loadingState');
    const recommendationsContent = document.getElementById('recommendationsContent');
    
    console.log('Toggling visibility...');
    loadingState.style.display = 'none';
    recommendationsContent.style.display = 'block';
    console.log(' Visibility toggled');

    // Display summary
    console.log(' Displaying summary...');
    displaySummary(recommendations);

    // Display all recommendation sections
    const grid = document.getElementById('recommendationsGrid');
    console.log('Recommendations grid element:', grid);
    grid.innerHTML = '';

    let cardsAdded = 0;

    // Technical Skills
    if (recommendations.missing_technical_skills && recommendations.missing_technical_skills.length > 0) {
        console.log(` Adding technical skills card (${recommendations.missing_technical_skills.length} items)`);
        grid.innerHTML += createSkillsCard(
            'Missing Technical Skills',
            'fas fa-code',
            'danger',
            recommendations.missing_technical_skills,
            'Skills highly valued in the job market'
        );
        cardsAdded++;
    }

    // Soft Skills
    if (recommendations.missing_soft_skills && recommendations.missing_soft_skills.length > 0) {
        console.log(` Adding soft skills card (${recommendations.missing_soft_skills.length} items)`);
        grid.innerHTML += createSkillsCard(
            'Soft Skills',
            'fas fa-users',
            'success',
            recommendations.missing_soft_skills,
            'Interpersonal and communication skills'
        );
        cardsAdded++;
    }

    // Education
    if (recommendations.missing_education && recommendations.missing_education.length > 0) {
        console.log(` Adding education card (${recommendations.missing_education.length} items)`);
        grid.innerHTML += createSkillsCard(
            'Education Gaps',
            'fas fa-graduation-cap',
            'warning',
            recommendations.missing_education,
            'Educational requirements from job postings'
        );
        cardsAdded++;
    }

    // Certifications
    if (recommendations.missing_certifications && recommendations.missing_certifications.length > 0) {
        console.log(` Adding certifications card (${recommendations.missing_certifications.length} items)`);
        grid.innerHTML += createSkillsCard(
            'Missing Certifications',
            'fas fa-certificate',
            'info',
            recommendations.missing_certifications,
            'Industry-recognized certifications'
        );
        cardsAdded++;
    }

    // Experience
    if (recommendations.missing_experience && recommendations.missing_experience.length > 0) {
        console.log(` Adding experience card (${recommendations.missing_experience.length} items)`);
        grid.innerHTML += createSkillsCard(
            'Experience Gaps',
            'fas fa-briefcase',
            'primary',
            recommendations.missing_experience,
            'Experience requirements from employers'
        );
        cardsAdded++;
    }

    // Priority Skills
    if (recommendations.priority_skills && recommendations.priority_skills.length > 0) {
        console.log(` Adding priority skills card (${recommendations.priority_skills.length} items)`);
        grid.innerHTML += createSkillsCard(
            'Priority Skills',
            'fas fa-star',
            'warning',
            recommendations.priority_skills,
            'Focus on these high-demand skills first',
            true
        );
        cardsAdded++;
    }

    // Learning Resources
    if (recommendations.learning_resources && recommendations.learning_resources.length > 0) {
        console.log(` Adding learning resources card (${recommendations.learning_resources.length} items)`);
        grid.innerHTML += createLearningResourcesCard(recommendations.learning_resources);
        cardsAdded++;
    }

    // Recommended Actions
    if (recommendations.recommended_actions && recommendations.recommended_actions.length > 0) {
        console.log(` Adding actions card (${recommendations.recommended_actions.length} items)`);
        grid.innerHTML += createActionsCard(recommendations.recommended_actions);
        cardsAdded++;
    }

    console.log(` Total cards added: ${cardsAdded}`);
    console.groupEnd();
}

function displaySummary(recommendations) {
    console.log('displaySummary called');
    
    const summaryCard = document.getElementById('summaryCard');
    console.log('Summary card element:', summaryCard);
    
    const counts = {
        skills: (recommendations.missing_technical_skills || []).length,
        certs: (recommendations.missing_certifications || []).length,
        actions: (recommendations.recommended_actions || []).length
    };
    console.log('Summary counts:', counts);

    summaryCard.innerHTML = `
        <div class="card-body text-white p-4">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h4 class="mb-2">
                        <i class="fas fa-lightbulb me-2"></i>Analysis Complete
                    </h4>
                    <p class="mb-0 opacity-90">We've analyzed job market requirements and identified areas for improvement</p>
                </div>
                <div class="col-md-4 text-md-end">
                    <div class="d-flex justify-content-md-end gap-3">
                        ${counts.skills > 0 ? `
                            <div class="text-center">
                                <div class="h3 mb-1">${counts.skills}</div>
                                <small class="opacity-75">Skills</small>
                            </div>
                        ` : ''}
                        ${counts.certs > 0 ? `
                            <div class="text-center">
                                <div class="h3 mb-1">${counts.certs}</div>
                                <small class="opacity-75">Certs</small>
                            </div>
                        ` : ''}
                        ${counts.actions > 0 ? `
                            <div class="text-center">
                                <div class="h3 mb-1">${counts.actions}</div>
                                <small class="opacity-75">Actions</small>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    console.log(' Summary HTML set');
}

function createSkillsCard(title, icon, color, skills, subtitle, isPriority = false) {
    console.log(`Creating skills card: ${title}, items: ${skills.length}`);
    
    return `
        <div class="col-lg-6 mb-4">
            <div class="recommendation-card h-100">
                <div class="card-header">
                    <h5 class="mb-0 text-${color}">
                        <i class="${icon} me-2"></i>${title}
                    </h5>
                    <small class="text-muted">${subtitle}</small>
                </div>
                <div class="card-body">
                    <div class="skills-list">
                        ${skills.map(skill => `
                            <div class="skill-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="skill-name">${skill}</span>
                                    <span class="badge bg-${color}-subtle text-${color}">
                                        ${isPriority ? 'High Priority' : getBadgeText(title)}
                                    </span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function createLearningResourcesCard(resources) {
    console.log(`Creating learning resources card with ${resources.length} resources`);
    console.log('Sample resource:', resources[0]);
    
    return `
        <div class="col-12 mb-4">
            <div class="recommendation-card">
                <div class="card-header">
                    <h5 class="mb-0 text-primary">
                        <i class="fas fa-book me-2"></i>Learning Resources
                    </h5>
                    <small class="text-muted">Recommended platforms and courses</small>
                </div>
                <div class="card-body">
                    <div class="row">
                        ${resources.map(resource => `
                            <div class="col-md-6 mb-3">
                                <div class="resource-item">
                                    <div class="resource-skill mb-1">${resource.skill || 'N/A'}</div>
                                    <div class="resource-platform">
                                        <i class="fas fa-external-link-alt me-1"></i>
                                        ${resource.resource || 'N/A'}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function createActionsCard(actions) {
    console.log(`Creating actions card with ${actions.length} actions`);
    console.log('Sample action:', actions[0]);
    
    return `
        <div class="col-12 mb-4">
            <div class="recommendation-card">
                <div class="card-header">
                    <h5 class="mb-0 text-dark">
                        <i class="fas fa-tasks me-2"></i>Recommended Actions
                    </h5>
                    <small class="text-muted">Specific steps to improve your profile</small>
                </div>
                <div class="card-body">
                    <div class="row">
                        ${actions.map((action, index) => `
                            <div class="col-md-6 mb-3">
                                <div class="action-item">
                                    <div class="d-flex align-items-start">
                                        <div class="action-number">${index + 1}</div>
                                        <div class="action-content">
                                            <p class="mb-0">${action}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getBadgeText(title) {
    const badges = {
        'Missing Technical Skills': 'Missing',
        'Soft Skills': 'Develop',
        'Education Gaps': 'Recommended',
        'Missing Certifications': 'Get Certified',
        'Experience Gaps': 'Build Experience'
    };
    return badges[title] || 'Required';
}

function showError(message) {
    console.error(' SHOWING ERROR:', message);
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('errorState').style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
}

console.log('=== RECOMMENDATIONS.JS FULLY LOADED ===');