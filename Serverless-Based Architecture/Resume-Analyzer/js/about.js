
document.addEventListener('DOMContentLoaded', function() {
    // Set current year
    document.getElementById('currentYear').textContent = new Date().getFullYear();
    
    // Update CTA buttons based on authentication
    updateCTAButtons();
    
    // Animate statistics on scroll
    animateStatistics();
    
    // Add hover effects
    addHoverEffects();
    
    // Smooth scroll for internal links
    setupSmoothScroll();
    
    // Typing effect for subtitle
    typeWriterEffect();
});

// Update CTA buttons based on authentication status
function updateCTAButtons() {
    const ctaButtons = document.getElementById('ctaButtons');
    const isAuth = window.ResumeAnalyzer && window.ResumeAnalyzer.isUserAuthenticated();
    
    if (isAuth) {
        ctaButtons.innerHTML = `
            <a href="upload.html" class="btn btn-success btn-lg px-5 me-sm-3" style="border-radius: 50px;">
                <i class="fas fa-upload me-2"></i>Upload Resume
            </a>
            <a href="account.html" class="btn btn-outline-primary btn-lg px-5" style="border-radius: 50px;">
                <i class="fas fa-user me-2"></i>My Dashboard
            </a>
        `;
    } else {
        ctaButtons.innerHTML = `
            <a href="register.html" class="btn btn-success btn-lg px-5 me-sm-3" style="border-radius: 50px;">
                <i class="fas fa-user-plus me-2"></i>Join the Research
            </a>
            <a href="login.html" class="btn btn-outline-primary btn-lg px-5" style="border-radius: 50px;">
                <i class="fas fa-sign-in-alt me-2"></i>Sign In
            </a>
        `;
    }
}

// Animate statistics on scroll
function animateStatistics() {
    const statNumbers = document.querySelectorAll('.stat-number');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateNumber(entry.target);
                observer.unobserve(entry.target);
            }
        });
    });

    statNumbers.forEach(stat => {
        observer.observe(stat);
    });
}

function animateNumber(element) {
    const target = element.textContent;
    const number = parseInt(target.replace(/\D/g, ''));
    const suffix = target.replace(/[\d,]/g, '');
    let current = 0;
    const increment = number / 50;
    const timer = setInterval(() => {
        current += increment;
        if (current >= number) {
            current = number;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current).toLocaleString() + suffix;
    }, 30);
}

// Add hover efects to cards
function addHoverEffects() {
    // Team cards
    const teamCards = document.querySelectorAll('.team-card');
    teamCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05))';
        });

        card.addEventListener('mouseleave', function() {
            this.style.background = '';
        });
    });

    // Tech items
    const techItems = document.querySelectorAll('.tech-item');
    techItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(102, 126, 234, 0.08)';
        });

        item.addEventListener('mouseleave', function() {
            this.style.background = '';
        });
    });
}

// Smooth scroll for internal links
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Add dynamic typing effect to the hero subtile
function typeWriterEffect() {
    const subtitle = document.querySelector('.page-header .lead');
    if (subtitle) {
        const originalText = subtitle.textContent;
        subtitle.textContent = '';
        let i = 0;
        const typeWriter = () => {
            if (i < originalText.length) {
                subtitle.textContent += originalText.charAt(i);
                i++;
                setTimeout(typeWriter, 50);
            }
        };
        setTimeout(typeWriter, 1000);
    }
}