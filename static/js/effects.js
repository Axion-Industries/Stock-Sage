// Professional Stock Market Dashboard Effects

class DashboardEffects {
    constructor() {
        this.mouseGlow = null;
        this.gridBackground = null;
        this.settings = this.loadSettings();
        this.init();
    }

    loadSettings() {
        const saved = localStorage.getItem('dashboard_settings');
        return saved ? JSON.parse(saved) : {
            theme: 'light',
            gridEffect: true,
            mouseGlow: true,
            animations: true,
            customBackground: null
        };
    }

    saveSettings() {
        localStorage.setItem('dashboard_settings', JSON.stringify(this.settings));
    }

    init() {
        this.createGridBackground();
        this.createMouseGlow();
        this.setupEventListeners();
        this.applyTheme();
        this.setupAnimations();
    }

    createGridBackground() {
        if (!this.settings.gridEffect) return;

        this.gridBackground = document.createElement('div');
        this.gridBackground.className = 'grid-background';
        document.body.appendChild(this.gridBackground);
    }

    createMouseGlow() {
        if (!this.settings.mouseGlow) return;

        this.mouseGlow = document.createElement('div');
        this.mouseGlow.className = 'mouse-glow';
        this.mouseGlow.style.opacity = '0';
        document.body.appendChild(this.mouseGlow);
    }

    setupEventListeners() {
        if (this.mouseGlow) {
            document.addEventListener('mousemove', (e) => {
                const x = e.clientX - 100;
                const y = e.clientY - 100;
                this.mouseGlow.style.left = x + 'px';
                this.mouseGlow.style.top = y + 'px';
                this.mouseGlow.style.opacity = '1';
            });

            document.addEventListener('mouseleave', () => {
                if (this.mouseGlow) {
                    this.mouseGlow.style.opacity = '0';
                }
            });
        }

        // Add glow effect to grid intersections
        if (this.gridBackground) {
            document.addEventListener('mousemove', (e) => {
                const rect = this.gridBackground.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                // Calculate grid intersection
                const gridX = Math.floor(x / 50) * 50;
                const gridY = Math.floor(y / 50) * 50;
                
                // Create temporary glow effect
                this.createGridGlow(gridX, gridY);
            });
        }
    }

    createGridGlow(x, y) {
        const glow = document.createElement('div');
        glow.style.position = 'absolute';
        glow.style.left = x + 'px';
        glow.style.top = y + 'px';
        glow.style.width = '4px';
        glow.style.height = '4px';
        glow.style.background = 'rgba(59, 130, 246, 0.8)';
        glow.style.borderRadius = '50%';
        glow.style.boxShadow = '0 0 20px rgba(59, 130, 246, 0.6)';
        glow.style.pointerEvents = 'none';
        glow.style.zIndex = '10';
        glow.style.transition = 'opacity 0.5s ease-out';
        
        this.gridBackground.appendChild(glow);
        
        // Fade out and remove
        setTimeout(() => {
            glow.style.opacity = '0';
            setTimeout(() => {
                if (glow.parentNode) {
                    glow.parentNode.removeChild(glow);
                }
            }, 500);
        }, 100);
    }

    applyTheme() {
        document.body.className = '';
        
        switch (this.settings.theme) {
            case 'dark':
                document.body.classList.add('theme-dark');
                break;
            case 'dark-green':
                document.body.classList.add('theme-dark-green');
                break;
            case 'custom':
                if (this.settings.customBackground) {
                    document.body.classList.add('theme-custom');
                    document.body.style.backgroundImage = `url(${this.settings.customBackground})`;
                }
                break;
            default:
                // Light theme (default)
                break;
        }
    }

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

// Utility functions for Streamlit integration
window.updateTheme = (theme) => {
    if (window.dashboardEffects) {
        window.dashboardEffects.updateSetting('theme', theme);
    }
};

window.toggleGridEffect = (enabled) => {
    if (window.dashboardEffects) {
        window.dashboardEffects.updateSetting('gridEffect', enabled);
    }
};

window.toggleMouseGlow = (enabled) => {
    if (window.dashboardEffects) {
        window.dashboardEffects.updateSetting('mouseGlow', enabled);
    }
};

window.setCustomBackground = (file) => {
    if (window.dashboardEffects) {
        window.dashboardEffects.setCustomBackground(file);
    }
};