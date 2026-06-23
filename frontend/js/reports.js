/**
 * Reports Controller
 */
class ReportsController {
    constructor() {
        if (!app.isAuthenticated()) {
            app.logout();
            return;
        }
        this.archives = [];
        this.init();
    }

    async init() {
        app.injectTopbar('Reporting Engine', { showSearch: false });
        await this.loadStats();
        this.renderArchives();
    }

    async loadStats() {
        try {
            const stats = await app.apiCall('/api/stats');
            const total = stats.total_events || 0;
            const critical = stats.events_by_severity?.CRITICAL || 0;
            const high = stats.events_by_severity?.HIGH || 0;
            const medium = stats.events_by_severity?.MEDIUM || 0;
            const low = stats.events_by_severity?.LOW || 0;

            // Calculate risk score
            let riskScore = 15;
            if (total > 0) {
                riskScore = Math.min(100, Math.round((critical * 18 + high * 9 + medium * 3 + low * 1)));
            }

            // Determine rating
            let rating = "LOW RISK (Operational status secure)";
            let ratingColor = "var(--success)";
            if (riskScore > 80) {
                rating = "CRITICAL THREAT LEVEL (Active attacks flagged)";
                ratingColor = "var(--severity-critical)";
            } else if (riskScore > 50) {
                rating = "HIGH THREAT LEVEL (Exploit vectors detected)";
                ratingColor = "var(--severity-high)";
            } else if (riskScore > 25) {
                rating = "MEDIUM THREAT LEVEL (Reconnaissance scanned)";
                ratingColor = "var(--accent)";
            }

            const scoreEl = document.getElementById('riskScoreVal');
            const ratingEl = document.getElementById('riskRatingVal');
            if (scoreEl && ratingEl) {
                scoreEl.textContent = riskScore;
                scoreEl.style.color = ratingColor;
                ratingEl.textContent = rating;
                ratingEl.style.color = ratingColor;
            }

            // Summary text
            const summaryEl = document.getElementById('summaryText');
            if (summaryEl) {
                summaryEl.innerHTML = `SOC telemetry analysis has logged <b>${total}</b> threat events. The machine learning pipeline identified <b>${critical} critical</b> and <b>${high} high-severity</b> incident vectors requiring administrator review.`;
            }

            // Generate strategic actions list
            const listEl = document.getElementById('recommendationsList');
            if (listEl) {
                const recs = [];
                if (critical > 0 || high > 0) {
                    recs.push("Deploy SOAR webhook IP block lists immediately to stop active SSH/API probers.");
                    recs.push("Verify credential complexity for admin accounts targeted during login scans.");
                }
                if (stats.events_by_service?.['demo-ecommerce'] > 0 || stats.events_by_service?.['DEMO_ECOMMERCE'] > 0) {
                    recs.push("Enable web application firewall rules (WAF) to drop payload patterns targeting public portals.");
                }
                recs.push("Ensure encrypted syslog stream connectivity is established on all decoy nodes.");
                recs.push("Validate Telegram alert configuration to maintain real-time notify response loops.");
                
                listEl.innerHTML = recs.map(r => `<li>${r}</li>`).join('');
            }

        } catch (error) {
            console.error("Stats load failed", error);
        }
    }

    async generate(format) {
        const sendTelegram = document.getElementById('sendTelegram').checked;
        const statusEl = document.getElementById('statusIndicator');
        const textEl = document.getElementById('statusText');
        
        statusEl.style.display = 'flex';
        textEl.textContent = `Compiling ${format.toUpperCase()} report...`;

        try {
            const response = await app.apiCall(`/api/reports/generate?format=${format}&send_telegram=${sendTelegram}`, {
                method: 'POST'
            });

            statusEl.style.display = 'none';

            let downloadUrl = '';
            if (response.status === 'processing') {
                app.showToast(`Report generation task started (Celery task: ${response.task_id})`, 'info');
                // Mock a file download for celery async simulation
                downloadUrl = '#';
            } else if (response.status === 'success') {
                app.showToast(`${format.toUpperCase()} report generated successfully.`, 'success');
                downloadUrl = response.download_url;
                
                // Trigger download via Blob to force browser to respect client-side filename
                if (response.download_url) {
                    try {
                        const fileUrl = `${app.apiBase}${response.download_url}`;
                        const token = app.getToken();
                        const headers = {};
                        if (token) {
                            headers['Authorization'] = `Bearer ${token}`;
                        }
                        
                        const fileResponse = await fetch(fileUrl, { headers });
                        if (!fileResponse.ok) throw new Error('Download request failed');
                        
                        const blob = await fileResponse.blob();
                        const blobUrl = URL.createObjectURL(blob);
                        
                        const downloadLink = document.createElement('a');
                        downloadLink.href = blobUrl;
                        const fileName = response.download_url.split('file=')[1] || `report.${format}`;
                        downloadLink.download = fileName;
                        
                        document.body.appendChild(downloadLink);
                        downloadLink.click();
                        document.body.removeChild(downloadLink);
                        
                        setTimeout(() => URL.revokeObjectURL(blobUrl), 100);
                    } catch (err) {
                        console.error('Blob download failed, falling back to iframe', err);
                        const iframe = document.createElement('iframe');
                        iframe.style.display = 'none';
                        iframe.src = `${app.apiBase}${response.download_url}`;
                        document.body.appendChild(iframe);
                        setTimeout(() => document.body.removeChild(iframe), 2000);
                    }
                }
            } else {
                app.showToast(response.message || 'Error generating report', 'error');
                return;
            }

            // Add to session archives
            this.archives.unshift({
                timestamp: new Date().toISOString(),
                format: format.toUpperCase(),
                channel: sendTelegram ? 'Secure Telegram & Local' : 'Local Download Only',
                status: 'Completed',
                download_url: downloadUrl
            });
            this.renderArchives();

        } catch (error) {
            statusEl.style.display = 'none';
            app.showToast(`Generation failed: ${error.message}`, 'error');
        }
    }

    renderArchives() {
        const tbody = document.getElementById('archivesBody');
        if (!tbody) return;

        if (this.archives.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center p-24 text-muted" style="text-align: center; padding: 24px; color: var(--text-muted);">No reports compiled in this workspace session yet.</td></tr>';
            return;
        }

        tbody.innerHTML = this.archives.map(arch => `
            <tr>
                <td class="font-mono text-muted">${app.formatDate(arch.timestamp)}</td>
                <td><span class="badge badge-medium" style="background: rgba(0, 188, 212, 0.15); color: var(--accent);">${arch.format}</span></td>
                <td class="text-muted text-xs">${arch.channel}</td>
                <td><span class="badge badge-low" style="color: var(--success); background: rgba(34,197,94,0.15);">${arch.status}</span></td>
                <td>
                    ${arch.download_url !== '#' ? (() => {
                        const filename = arch.download_url.split('file=')[1] || '';
                        return `<a href="${app.apiBase}${arch.download_url}" download="${filename}" class="btn btn-secondary btn-sm">Download</a>`;
                    })() : `<span class="text-muted text-xs">Task Pending</span>`}
                </td>
            </tr>
        `).join('');
    }
}

const reports = new ReportsController();
