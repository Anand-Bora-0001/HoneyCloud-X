/**
 * Settings Controller
 */
class SettingsController {
    constructor() {
        if (!app.isAuthenticated()) {
            app.logout();
            return;
        }
        this.init();
    }

    async init() {
        app.injectTopbar('Platform Settings', { showSearch: false });
        this.loadProfile();
        this.loadTelegramConfig();
        this.loadPreferences();
        this.loadSensors();
        this.loadThemeSettings();
        
        document.getElementById('tgForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveTelegram();
        });
    }

    switchTab(tabId, btnElement) {
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
        
        document.getElementById(`tab-${tabId}`).classList.add('active');
        btnElement.classList.add('active');
    }

    async loadProfile() {
        try {
            const user = await app.apiCall('/auth/me');
            document.getElementById('profileUser').value = user.username;
            document.getElementById('profileEmail').value = user.email || 'N/A';
            document.getElementById('profileRole').value = (user.role || 'administrator').toUpperCase();
        } catch (error) {
            console.error("Profile load failed", error);
        }
    }

    /* --- Decoy Sensors --- */

    async loadSensors() {
        const tbody = document.getElementById('sensorsListBody');
        if (!tbody) return;

        try {
            const services = await app.apiCall('/api/saas/services');
            
            if (services.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center p-24 text-muted" style="text-align: center; padding: 24px;">No active decoy sensors registered. Register one above.</td></tr>';
                return;
            }

            tbody.innerHTML = services.map(svc => {
                const dateStr = app.formatDate(svc.created_at || new Date().toISOString());
                return `
                    <tr>
                        <td class="cell-primary font-mono">${svc.name}</td>
                        <td><span class="badge badge-medium" style="background: rgba(0, 188, 212, 0.1); color: var(--accent);">${svc.service_type.toUpperCase()}</span></td>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <input type="password" class="form-input font-mono" style="padding: 4px 8px; width: 180px; font-size: 0.75rem;" readonly value="${svc.api_key}" id="key-${svc.id}">
                                <button class="btn btn-secondary btn-sm" style="padding: 2px 6px;" onclick="settings.toggleKeyVisibility(${svc.id})">Reveal</button>
                                <button class="btn btn-secondary btn-sm" style="padding: 2px 6px;" onclick="settings.copyKeyToClipboard('${svc.api_key}')">Copy</button>
                            </div>
                        </td>
                        <td class="text-muted text-xs">${dateStr}</td>
                        <td>
                            <div style="display: flex; gap: 8px;">
                                <button class="btn btn-secondary btn-sm" onclick="settings.regenerateSensorKey(${svc.id})">Regenerate</button>
                                <button class="btn btn-danger btn-sm" onclick="settings.deleteSensor(${svc.id})">Deactivate</button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');

        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center p-24 text-danger" style="text-align: center; padding: 24px;">Failed to load sensors: ${error.message}</td></tr>`;
        }
    }

    toggleKeyVisibility(id) {
        const input = document.getElementById(`key-${id}`);
        if (input) {
            input.type = input.type === 'password' ? 'text' : 'password';
        }
    }

    copyKeyToClipboard(key) {
        navigator.clipboard.writeText(key).then(() => {
            app.showToast('Sensor API Key copied to clipboard', 'success');
        }).catch(() => {
            app.showToast('Failed to copy key.', 'error');
        });
    }

    openSensorModal(open) {
        const modal = document.getElementById('sensorModal');
        if (modal) {
            modal.classList.toggle('open', open);
        }
    }

    async createSensor() {
        const name = document.getElementById('sensorName').value.trim();
        const service_type = document.getElementById('sensorType').value;
        const description = document.getElementById('sensorDesc').value.trim();

        if (!name) {
            app.showToast('Sensor name is required', 'warning');
            return;
        }

        try {
            await app.apiCall('/api/saas/services', {
                method: 'POST',
                body: JSON.stringify({ name, service_type, description })
            });

            app.showToast('Decoy sensor registered successfully!', 'success');
            this.openSensorModal(false);
            
            // reset form
            document.getElementById('sensorName').value = '';
            document.getElementById('sensorDesc').value = '';

            await this.loadSensors();
        } catch (error) {
            app.showToast(error.message, 'error');
        }
    }

    async regenerateSensorKey(id) {
        if (!confirm('Are you sure you want to regenerate this credentials key? Legacy sensors using the old key will be locked out immediately.')) return;

        try {
            const res = await app.apiCall(`/api/saas/services/${id}/regenerate-key`, { method: 'POST' });
            app.showToast(`API Key regenerated for ${res.name}`, 'success');
            await this.loadSensors();
        } catch (error) {
            app.showToast(error.message, 'error');
        }
    }

    async deleteSensor(id) {
        if (!confirm('Are you sure you want to deactivate this decoy sensor? Action is irreversible.')) return;

        try {
            await app.apiCall(`/api/saas/services/${id}`, { method: 'DELETE' });
            app.showToast('Decoy sensor deactivated successfully', 'success');
            await this.loadSensors();
        } catch (error) {
            app.showToast(error.message, 'error');
        }
    }

    /* --- Theme Settings --- */

    loadThemeSettings() {
        const theme = localStorage.getItem('hc_theme') || 'default';
        const grid = localStorage.getItem('hc_grid') === 'true';

        document.getElementById('themeSelect').value = theme;
        document.getElementById('toggleGrid').checked = grid;

        this.changeSubTheme(theme);
        this.toggleSimpleGrid(grid);
    }

    changeSubTheme(theme) {
        if (theme === 'midnight-amber') {
            document.documentElement.style.setProperty('--accent', '#FFC14D');
            document.documentElement.style.setProperty('--accent-hover', '#F6A623');
            document.documentElement.style.setProperty('--accent-light', 'rgba(255,193,77,0.1)');
            document.documentElement.style.setProperty('--border-active', 'rgba(255,193,77,0.5)');
            document.documentElement.style.setProperty('--bg-primary', '#070A0E');
            document.documentElement.style.setProperty('--bg-surface', '#0D1117');
        } else if (theme === 'obsidian') {
            document.documentElement.style.setProperty('--accent', '#C47B1A');
            document.documentElement.style.setProperty('--accent-hover', '#A3620F');
            document.documentElement.style.setProperty('--accent-light', 'rgba(196,123,26,0.1)');
            document.documentElement.style.setProperty('--border-active', 'rgba(196,123,26,0.5)');
            document.documentElement.style.setProperty('--bg-primary', '#050505');
            document.documentElement.style.setProperty('--bg-surface', '#0C0C0C');
        } else {
            // default Honey Gold
            document.documentElement.style.setProperty('--accent', '#F6A623');
            document.documentElement.style.setProperty('--accent-hover', '#E8912D');
            document.documentElement.style.setProperty('--accent-light', 'rgba(246,166,35,0.1)');
            document.documentElement.style.setProperty('--border-active', 'rgba(246,166,35,0.5)');
            document.documentElement.style.setProperty('--bg-primary', '#0B0F14');
            document.documentElement.style.setProperty('--bg-surface', '#111827');
        }
        localStorage.setItem('hc_theme', theme);
    }

    toggleSimpleGrid(show) {
        if (show) {
            document.body.style.backgroundImage = 'radial-gradient(var(--border) 1px, transparent 1px)';
            document.body.style.backgroundSize = '24px 24px';
        } else {
            document.body.style.backgroundImage = 'none';
        }
        localStorage.setItem('hc_grid', show);
    }

    /* --- Telegram --- */

    async loadTelegramConfig() {
        try {
            const config = await app.apiCall('/api/telegram/config');
            if (config.configured) {
                document.getElementById('tgStatusBadge').classList.remove('hidden');
                document.getElementById('tgChat').value = config.chat_id || '';
                if (config.bot_token_set) {
                    document.getElementById('tgToken').placeholder = '••••••••••••••••••••••••••••••••';
                }
            }
        } catch (error) {
            console.error("TG config load failed", error);
        }
    }

    async validateTelegram() {
        const token = document.getElementById('tgToken').value;
        const chat = document.getElementById('tgChat').value;
        
        if (!token || !chat) {
            app.showToast('Token and Chat ID required for validation', 'warning');
            return;
        }

        try {
            const res = await app.apiCall('/api/telegram/validate', {
                method: 'POST',
                body: JSON.stringify({ bot_token: token, chat_id: chat })
            });
            
            app.showToast(`Verified bot @${res.bot_username}`, 'success');
            document.getElementById('tgSaveBtn').disabled = false;
        } catch (error) {
            app.showToast(error.message, 'error');
        }
    }

    async saveTelegram() {
        const token = document.getElementById('tgToken').value;
        const chat = document.getElementById('tgChat').value;

        try {
            await app.apiCall('/api/telegram/configure', {
                method: 'POST',
                body: JSON.stringify({ bot_token: token, chat_id: chat })
            });
            
            app.showToast('Telegram integration configured successfully', 'success');
            document.getElementById('tgStatusBadge').classList.remove('hidden');
            document.getElementById('tgSaveBtn').disabled = true;
        } catch (error) {
            app.showToast(error.message, 'error');
        }
    }

    async testTelegram() {
        try {
            await app.apiCall('/api/alerts/test-telegram', { method: 'POST' });
            app.showToast('Test signal dispatched to Telegram', 'success');
        } catch (error) {
            try {
                await app.apiCall('/api/telegram/test', { method: 'POST' });
                app.showToast('Test signal dispatched to Telegram', 'success');
            } catch (err2) {
                app.showToast(error.message || err2.message, 'error');
            }
        }
    }

    /* --- Email --- */

    async testEmail() {
        const email = document.getElementById('testEmail').value;
        const logPanel = document.getElementById('smtpLogPanel');
        
        if (!email) {
            app.showToast('Enter a destination email address', 'warning');
            return;
        }
        
        if (logPanel) {
            logPanel.style.display = 'none';
            logPanel.textContent = '';
        }

        try {
            app.showToast('Dispatched test email alert...', 'info');
            const res = await app.apiCall('/api/alerts/test-email', {
                method: 'POST',
                body: JSON.stringify({ email_address: email, save_email: true })
            });
            
            if (res.status === 'success') {
                app.showToast('Email Sent Successfully', 'success');
                // Reload config so saved email shows up
                await this.loadPreferences();
            } else {
                app.showToast('Email Delivery Failed', 'error');
                if (logPanel) {
                    logPanel.style.display = 'block';
                    logPanel.textContent = `Error: ${res.message}\nDetails: ${res.details || 'N/A'}`;
                }
            }
        } catch (error) {
            app.showToast('Email Delivery Failed', 'error');
            if (logPanel) {
                logPanel.style.display = 'block';
                logPanel.textContent = `Exception: ${error.message}`;
            }
        }
    }

    toggleSeverityFilters(selected) {
        const critOnly = document.getElementById('prefCriticalOnly');
        const highCrit = document.getElementById('prefHighCritical');
        
        if (selected === 'critical' && critOnly.checked) {
            highCrit.checked = false;
        } else if (selected === 'high' && highCrit.checked) {
            critOnly.checked = false;
        }
    }

    async loadPreferences() {
        try {
            const config = await app.apiCall('/api/alerts/config');
            document.getElementById('prefTelegramEnabled').checked = config.telegram_enabled || false;
            document.getElementById('prefEmailEnabled').checked = config.email_enabled || false;
            document.getElementById('prefCriticalOnly').checked = config.alert_on_critical && !config.alert_on_high;
            document.getElementById('prefHighCritical').checked = config.alert_on_critical && config.alert_on_high;
            document.getElementById('prefDailySummary').checked = config.daily_summary_enabled || false;
            document.getElementById('prefWeeklyReport').checked = config.weekly_report_enabled || false;
            
            if (config.saved_emails && config.saved_emails.length > 0) {
                document.getElementById('testEmail').value = config.saved_emails[0];
            }
        } catch (error) {
            console.error("Preferences load failed", error);
        }
    }

    async savePreferences() {
        const telegram_enabled = document.getElementById('prefTelegramEnabled').checked;
        const email_enabled = document.getElementById('prefEmailEnabled').checked;
        const critOnly = document.getElementById('prefCriticalOnly').checked;
        const highCrit = document.getElementById('prefHighCritical').checked;
        const daily_summary_enabled = document.getElementById('prefDailySummary').checked;
        const weekly_report_enabled = document.getElementById('prefWeeklyReport').checked;

        // Map severity filters:
        // alert_on_critical: true if criticalOnly or highCritical, or default
        const alert_on_critical = true;
        const alert_on_high = highCrit;
        const alert_on_medium = false;
        const alert_on_low = false;

        const email = document.getElementById('testEmail').value;
        const saved_emails = email ? [email] : [];

        const payload = {
            telegram_enabled,
            email_enabled,
            alert_on_critical,
            alert_on_high,
            alert_on_medium,
            alert_on_low,
            daily_summary_enabled,
            weekly_report_enabled,
            saved_emails
        };

        try {
            await app.apiCall('/api/alerts/config', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            app.showToast('Notification preferences updated successfully', 'success');
        } catch (error) {
            app.showToast(error.message, 'error');
        }
    }
}

const settings = new SettingsController();
