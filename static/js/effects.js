// Simplified Dashboard Effects - Dark Theme Only

class DashboardEffects {
    constructor() {
        this.init();
    }

    init() {
        this.setupAnimations();
    }

    // Removed grid and mouse glow effects

    setupAnimations() {
        if (!this.settings.animations) return;

        // Add intersection observer for animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in');
                }
            });
        }, {
            threshold: 0.1
        });

        // Observe all metric containers and charts
        document.querySelectorAll('.metric-container, .chart-container').forEach(el => {
            observer.observe(el);
        });
    }

    updateSetting(key, value) {
        this.settings[key] = value;
        this.saveSettings();
        
        switch (key) {
            case 'theme':
                this.applyTheme();
                break;
            case 'gridEffect':
                if (value) {
                    this.createGridBackground();
                } else if (this.gridBackground) {
                    this.gridBackground.remove();
                    this.gridBackground = null;
                }
                break;
            case 'mouseGlow':
                if (value) {
                    this.createMouseGlow();
                    this.setupEventListeners();
                } else if (this.mouseGlow) {
                    this.mouseGlow.remove();
                    this.mouseGlow = null;
                }
                break;
            case 'customBackground':
                if (this.settings.theme === 'custom') {
                    this.applyTheme();
                }
                break;
        }
    }

    setCustomBackground(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.updateSetting('customBackground', e.target.result);
            this.updateSetting('theme', 'custom');
        };
        reader.readAsDataURL(file);
    }

    // Animation utilities
    animateValue(element, start, end, duration) {
        const startTime = performance.now();
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = start + (end - start) * this.easeOutCubic(progress);
            element.textContent = Math.floor(current).toLocaleString();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        requestAnimationFrame(animate);
    }

    easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    // Pulse effect for alerts
    pulseElement(element, color = '#3b82f6') {
        const original = element.style.boxShadow;
        element.style.transition = 'box-shadow 0.3s ease';
        element.style.boxShadow = `0 0 20px ${color}`;
        
        setTimeout(() => {
            element.style.boxShadow = original;
        }, 1000);
    }

    // Typing effect for text
    typeText(element, text, speed = 50) {
        element.textContent = '';
        let i = 0;
        const type = () => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        };
        type();
    }
}

// Initialize effects when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardEffects = new DashboardEffects();
});

// Removed theme switching utilities - dark theme is permanent