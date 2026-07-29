/**
 * Net Worth Tennis - Report Issue Button
 * Floating tennis ball button for users to report bugs/issues
 */

(function() {
    'use strict';

    // Get user info from localStorage if available
    function getUserInfo() {
        const playerStr = localStorage.getItem('networth_player');
        if (playerStr) {
            try {
                const player = JSON.parse(playerStr);
                return {
                    email: player.email || 'Anonymous',
                    name: player.name || ''
                };
            } catch (e) {
                console.error('Failed to parse player info:', e);
            }
        }
        return { email: 'Anonymous', name: '' };
    }

    // Create floating button
    function createButton() {
        const button = document.createElement('button');
        button.id = 'report-issue-button';
        button.setAttribute('aria-label', 'Report an issue');
        button.innerHTML = '🎾 Call Umpire';
        button.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            background: linear-gradient(135deg, #d165a4, #ec613e);
            color: white;
            border: none;
            border-radius: 50px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(209, 101, 164, 0.4);
            transition: all 0.3s ease;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;

        // Hover effects
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'scale(1.05)';
            button.style.boxShadow = '0 6px 16px rgba(209, 101, 164, 0.5)';
        });

        button.addEventListener('mouseleave', () => {
            button.style.transform = 'scale(1)';
            button.style.boxShadow = '0 4px 12px rgba(209, 101, 164, 0.4)';
        });

        button.addEventListener('click', openModal);
        document.body.appendChild(button);
    }

    // Create modal
    function createModal() {
        const modal = document.createElement('div');
        modal.id = 'report-issue-modal';
        modal.style.cssText = `
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 10000;
            justify-content: center;
            align-items: center;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;

        content.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #d165a4;">🎾 Call the Umpire</h2>
                <button id="close-modal" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #999;">&times;</button>
            </div>
            <p style="color: #666; margin-bottom: 20px;">Found a bug or have an issue? Let us know!</p>
            <form id="issue-form">
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #333;">Your Name</label>
                    <input type="text" id="reporter-name" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px;" placeholder="Your name">
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #333;">Your Email</label>
                    <input type="email" id="reporter-email" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px;" placeholder="your@email.com">
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #333;">Message</label>
                    <textarea id="issue-message" rows="4" required style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; resize: vertical;" placeholder="Describe the issue..."></textarea>
                </div>
                <button type="submit" style="width: 100%; background: linear-gradient(135deg, #d165a4, #ec613e); color: white; border: none; padding: 12px; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer;">
                    Send Report
                </button>
            </form>
            <div id="form-status" style="margin-top: 15px; text-align: center; display: none;"></div>
        `;

        modal.appendChild(content);
        document.body.appendChild(modal);

        // Event listeners
        document.getElementById('close-modal').addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });

        document.getElementById('issue-form').addEventListener('submit', handleSubmit);

        document.querySelectorAll('[data-call-umpire]').forEach((trigger) => {
            trigger.addEventListener('click', openModal);
        });
    }

    function openModal() {
        const modal = document.getElementById('report-issue-modal');
        const user = getUserInfo();

        // Pre-fill user info
        document.getElementById('reporter-name').value = user.name;
        document.getElementById('reporter-email').value = user.email === 'Anonymous' ? '' : user.email;

        modal.style.display = 'flex';
        document.getElementById('issue-message').focus();
    }

    function closeModal() {
        document.getElementById('report-issue-modal').style.display = 'none';
        document.getElementById('form-status').style.display = 'none';
        document.getElementById('issue-form').reset();
    }

    async function handleSubmit(e) {
        e.preventDefault();

        const statusEl = document.getElementById('form-status');
        const submitBtn = e.target.querySelector('button[type="submit"]');

        const data = {
            reporter_name: document.getElementById('reporter-name').value,
            reporter_email: document.getElementById('reporter-email').value || 'Anonymous',
            page_path: window.location.pathname,
            message: document.getElementById('issue-message').value
        };

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending...';
        statusEl.style.display = 'block';
        statusEl.innerHTML = '<span style="color: #666;">Sending report...</span>';

        try {
            const response = await fetch('/api/system', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'report_issue', ...data })
            });

            const result = await response.json();

            if (result.success) {
                statusEl.innerHTML = '<span style="color: #22c55e;">✓ Report sent! Thanks for helping improve Net Worth Tennis.</span>';
                setTimeout(() => {
                    closeModal();
                }, 2000);
            } else {
                throw new Error(result.error || 'Failed to send report');
            }
        } catch (error) {
            statusEl.innerHTML = `<span style="color: #ef4444;">✗ Failed to send: ${error.message}</span>`;
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Send Report';
        }
    }

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            if (document.body.dataset.page !== 'support') createButton();
            createModal();
        });
    } else {
        if (document.body.dataset.page !== 'support') createButton();
        createModal();
    }
})();
