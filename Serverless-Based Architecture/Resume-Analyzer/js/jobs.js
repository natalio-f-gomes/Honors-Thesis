document.addEventListener('DOMContentLoaded', async function() {
    // Check auth
    if (!window.CognitoAuth || !window.CognitoAuth.isAuthenticated()) {
        window.location.href = 'index.html?message=Please log in';
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const resumeId = urlParams.get('resumeId');

    if (!resumeId) {
        alert('No resume ID provided');
        window.location.href = 'account.html';
        return;
    }

    await loadJobs(resumeId);
});

async function loadJobs(resumeId) {
    try {
        const token = localStorage.getItem('idToken');
        
        const response = await fetch(
            `https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/get-jobs-data?resumeId=${resumeId}`,
            {
                headers: { 'Authorization': `Bearer ${token}` }
            }
        );

        if (!response.ok) throw new Error('Failed to load jobs');

        const jobsData = await response.json();
        
        displayJobs(jobsData.jobs, jobsData.search_params);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loadingState').innerHTML = `
            <div class="alert alert-danger">
                <h4>Error Loading Jobs</h4>
                <p>${error.message}</p>
                <a href="account.html" class="btn btn-primary">Back to Account</a>
            </div>
        `;
    }
}

async function loadJobs(resumeId) {
    try {
        const token = localStorage.getItem('idToken');
        
        const response = await fetch(
            `https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/get-jobs-data?resumeId=${resumeId}`,
            {
                headers: { 'Authorization': `Bearer ${token}` }
            }
        );

        if (!response.ok) throw new Error('Failed to load jobs');

        const jobsData = await response.json();
        
        displayJobs(jobsData.jobs, jobsData.search_params);
        
        // Set recommendations button link - use setAttribute to avoid selector issues
        const recBtn = document.getElementById('viewRecommendationsBtn');
        if (recBtn) {
            recBtn.setAttribute('href', `recommendations.html?resumeId=${resumeId}`);
        }

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loadingState').innerHTML = `
            <div class="alert alert-danger">
                <h4>Error Loading Jobs</h4>
                <p>${error.message}</p>
                <a href="account.html" class="btn btn-primary">Back to Account</a>
            </div>
        `;
    }
}


function displayJobs(jobs, searchParams) {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('jobsContent').style.display = 'block';
    
    document.getElementById('jobCount').textContent = 
        `Found ${jobs.length} ${searchParams.experience_level} level ${searchParams.career_field} jobs`;

    const jobsList = document.getElementById('jobsList');
    
    jobs.forEach(job => {
        const jobCard = createJobCard(job);
        jobsList.innerHTML += jobCard;
    });
}

function createJobCard(job) {
    // Helper function to format values, replace null/undefined with N/A
    const format = (value) => value || 'N/A';
    const formatArray = (arr) => arr && arr.length > 0 ? arr : [];
    
    // Format salary
    let salaryInfo = '';
    if (job.job_min_salary && job.job_max_salary) {
        salaryInfo = `<p class="mb-1"><strong>Salary:</strong> $${job.job_min_salary.toLocaleString()} - $${job.job_max_salary.toLocaleString()}${job.job_salary_period ? ` / ${job.job_salary_period}` : ''}</p>`;
    } else if (job.job_salary) {
        salaryInfo = `<p class="mb-1"><strong>Salary:</strong> ${job.job_salary}</p>`;
    }
    
    // Format benefits
    let benefitsHTML = '';
    const benefits = formatArray(job.job_benefits);
    if (benefits.length > 0) {
        benefitsHTML = `
            <div class="mb-2">
                <strong>Benefits:</strong>
                <div class="mt-1">
                    ${benefits.map(b => `<span class="badge bg-success me-1">${b.replace(/_/g, ' ')}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    // Format job highlights
    let highlightsHTML = '';
    if (job.job_highlights) {
        const sections = [];
        
        if (job.job_highlights.Qualifications && job.job_highlights.Qualifications.length > 0) {
            sections.push(`
                <div class="mb-2">
                    <strong class="text-primary">Qualifications:</strong>
                    <ul class="mb-0 mt-1">
                        ${job.job_highlights.Qualifications.slice(0, 5).map(q => `<li>${q}</li>`).join('')}
                    </ul>
                </div>
            `);
        }
        
        if (job.job_highlights.Responsibilities && job.job_highlights.Responsibilities.length > 0) {
            sections.push(`
                <div class="mb-2">
                    <strong class="text-success">Responsibilities:</strong>
                    <ul class="mb-0 mt-1">
                        ${job.job_highlights.Responsibilities.slice(0, 5).map(r => `<li>${r}</li>`).join('')}
                    </ul>
                </div>
            `);
        }
        
        if (job.job_highlights.Benefits && job.job_highlights.Benefits.length > 0) {
            sections.push(`
                <div class="mb-2">
                    <strong class="text-warning">Benefits:</strong>
                    <ul class="mb-0 mt-1">
                        ${job.job_highlights.Benefits.slice(0, 5).map(b => `<li>${b}</li>`).join('')}
                    </ul>
                </div>
            `);
        }
        
        if (sections.length > 0) {
            highlightsHTML = `
                <div class="collapse" id="details-${job.job_id}">
                    <div class="card card-body mt-2 bg-light">
                        ${sections.join('')}
                    </div>
                </div>
            `;
        }
    }
    
    return `
        <div class="col-12 mb-4">
            <div class="card shadow-sm border-0" style="border-radius: 15px; overflow: hidden;">
                <div class="card-body p-4">
                    <div class="row">
                        <div class="col-md-2 text-center mb-3 mb-md-0">
                            ${job.employer_logo ? 
                                `<img src="${job.employer_logo}" alt="${format(job.employer_name)}" class="img-fluid rounded" style="max-width: 80px;">` :
                                `<div class="bg-primary text-white rounded d-flex align-items-center justify-content-center" style="width: 80px; height: 80px; font-size: 2rem;">
                                    <i class="fas fa-building"></i>
                                </div>`
                            }
                        </div>
                        <div class="col-md-7">
                            <h5 class="card-title mb-2">${format(job.job_title)}</h5>
                            <h6 class="text-primary mb-2">
                                ${format(job.employer_name)}
                                ${job.employer_website ? `<a href="${job.employer_website}" target="_blank" class="ms-2"><i class="fas fa-external-link-alt"></i></a>` : ''}
                            </h6>
                            
                            <div class="mb-2">
                                <i class="fas fa-map-marker-alt text-muted me-1"></i>
                                <span>${format(job.job_city)}, ${format(job.job_state)}</span>
                                ${job.job_is_remote ? '<span class="badge bg-success ms-2">Remote</span>' : ''}
                            </div>
                            
                            <div class="mb-2">
                                <i class="fas fa-briefcase text-muted me-1"></i>
                                <span>${formatArray(job.job_employment_types).join(', ') || format(job.job_employment_type)}</span>
                            </div>
                            
                            ${job.job_posted_at ? `
                                <div class="mb-2">
                                    <i class="fas fa-clock text-muted me-1"></i>
                                    <span>Posted ${job.job_posted_at}</span>
                                </div>
                            ` : ''}
                            
                            ${salaryInfo}
                            ${benefitsHTML}
                            
                            ${job.job_description ? `
                                <p class="card-text mt-3 text-muted">${job.job_description.substring(0, 250)}...</p>
                            ` : ''}
                        </div>
                        <div class="col-md-3 text-center">
                            <a href="${job.job_apply_link}" target="_blank" class="btn btn-primary w-100 mb-2" style="border-radius: 50px;">
                                <i class="fas fa-external-link-alt me-1"></i>Apply Now
                            </a>
                            
                            ${job.job_google_link ? `
                                <a href="${job.job_google_link}" target="_blank" class="btn btn-outline-secondary w-100 mb-2" style="border-radius: 50px;">
                                    <i class="fab fa-google me-1"></i>View on Google
                                </a>
                            ` : ''}
                            
                            ${highlightsHTML ? `
                                <button class="btn btn-outline-info w-100" type="button" data-bs-toggle="collapse" data-bs-target="#details-${job.job_id}" style="border-radius: 50px;">
                                    <i class="fas fa-info-circle me-1"></i>More Details
                                </button>
                            ` : ''}
                            
                            <div class="mt-3">
                                <small class="text-muted">Publisher: ${format(job.job_publisher)}</small>
                            </div>
                        </div>
                    </div>
                    
                    ${highlightsHTML}
                </div>
            </div>
        </div>
    `;
}