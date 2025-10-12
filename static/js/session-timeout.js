/**
 * Session Timeout Management
 * Monitors user session and provides warnings before automatic logout
 */

class SessionManager {
    constructor() {
        this.warningShown = false;
        this.warningModal = null;
        this.checkInterval = 60000; // Check every minute
        this.intervalId = null;
        this.init();
    }

    init() {
        // Only initialize on authenticated pages
        if (document.querySelector('[data-user-authenticated]')) {
            this.startMonitoring();
            this.createWarningModal();
        }
    }

    startMonitoring() {
        // Check session status immediately and then at intervals
        this.checkSessionStatus();
        this.intervalId = setInterval(() => {
            this.checkSessionStatus();
        }, this.checkInterval);
    }

    async checkSessionStatus() {
        try {
            const response = await fetch('/api/session-status');
            const data = await response.json();

            if (data.status === 'expired') {
                this.handleSessionExpired();
            } else if (data.status === 'warning') {
                this.showWarning(data.remaining_seconds);
            } else if (data.status === 'active') {
                this.hideWarning();
            }
        } catch (error) {
            console.error('Session status check failed:', error);
        }
    }

    showWarning(remainingSeconds) {
        if (!this.warningShown) {
            this.warningShown = true;
            const minutes = Math.ceil(remainingSeconds / 60);
            
            this.updateWarningModal(`Your session will expire in ${minutes} minute${minutes !== 1 ? 's' : ''} due to inactivity.`);
            this.warningModal.style.display = 'block';
        }
    }

    hideWarning() {
        if (this.warningShown) {
            this.warningShown = false;
            this.warningModal.style.display = 'none';
        }
    }

    handleSessionExpired() {
        this.stopMonitoring();
        alert('Your session has expired. You will be redirected to the login page.');
        window.location.href = '/login';
    }

    async extendSession() {
        try {
            const response = await fetch('/api/extend-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                this.hideWarning();
                console.log('Session extended successfully');
            }
        } catch (error) {
            console.error('Failed to extend session:', error);
        }
    }

    createWarningModal() {
        // Create modal HTML
        const modalHTML = `
            <div id="session-warning-modal" style="
                display: none;
                position: fixed;
                z-index: 9999;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
            ">
                <div style="
                    background-color: #fefefe;
                    margin: 15% auto;
                    padding: 20px;
                    border: 1px solid #888;
                    border-radius: 8px;
                    width: 400px;
                    max-width: 90%;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                ">
                    <h3 style="color: #f0ad4e; margin-top: 0;">⚠️ Session Warning</h3>
                    <p id="session-warning-message"></p>
                    <div style="margin-top: 20px;">
                        <button id="extend-session-btn" style="
                            background-color: #5cb85c;
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            margin-right: 10px;
                            border-radius: 4px;
                            cursor: pointer;
                        ">Stay Logged In</button>
                        <button id="logout-now-btn" style="
                            background-color: #d9534f;
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 4px;
                            cursor: pointer;
                        ">Logout Now</button>
                    </div>
                </div>
            </div>
        `;

        // Insert modal into page
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.warningModal = document.getElementById('session-warning-modal');

        // Add event listeners
        document.getElementById('extend-session-btn').addEventListener('click', () => {
            this.extendSession();
        });

        document.getElementById('logout-now-btn').addEventListener('click', () => {
            window.location.href = '/logout';
        });
    }

    updateWarningModal(message) {
        const messageElement = document.getElementById('session-warning-message');
        if (messageElement) {
            messageElement.textContent = message;
        }
    }

    stopMonitoring() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    // Activity tracking - reset timeout on user activity
    trackActivity() {
        // Debounce activity tracking
        clearTimeout(this.activityTimeout);
        this.activityTimeout = setTimeout(() => {
            // Only track significant activity, not just mouse movements
            this.extendSession();
        }, 30000); // 30 seconds debounce
    }
}

// Initialize session manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.sessionManager = new SessionManager();

    // Track user activity for session extension
    const activityEvents = ['click', 'keydown', 'scroll'];
    activityEvents.forEach(event => {
        document.addEventListener(event, () => {
            if (window.sessionManager) {
                window.sessionManager.trackActivity();
            }
        }, { passive: true });
    });
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.sessionManager) {
        window.sessionManager.stopMonitoring();
    }
});