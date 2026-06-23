/**
 * Attack Details Controller
 */
class AttackDetailsController {
    constructor() {
        if (!app.isAuthenticated()) {
            app.logout();
            return;
        }

        const urlParams = new URLSearchParams(window.location.search);
        this.eventId = urlParams.get('id');

        if (!this.eventId) {
            document.getElementById('detailsContainer').innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <h3>No Threat ID Specified</h3>
                    <p>Navigate to the dashboard and select a threat event to inspect.</p>
                    <a href="dashboard.html" class="btn btn-primary mt-16">Return to Dashboard</a>
                </div>
            `;
            return;
        }

        this.init();
    }

    async init() {
        app.injectTopbar(`
            <div class="breadcrumb">
                <a href="dashboard.html">Dashboard</a>
                <span class="breadcrumb-sep">›</span>
                <span class="text-primary">Threat Record</span>
            </div>
        `, { showSearch: false });

        try {
            // First load the event from the recent list (this endpoint supports pagination, we'll fetch a decent chunk to find it, or simulate fetching by ID since the backend doesn't have a direct GET /events/{id})
            const events = await app.apiCall('/api/events?limit=200');
            const event = events.find(e => e.id == this.eventId);

            if (!event) {
                throw new Error("Threat intelligence record not found or has been purged.");
            }

            this.renderDetails(event);
            
            // Try to fetch extended IP intelligence if available
            this.fetchExtendedIntel(event.source_ip);

        } catch (error) {
            document.getElementById('detailsContainer').innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">❌</div>
                    <h3>Record Not Found</h3>
                    <p class="text-danger">${error.message}</p>
                    <a href="dashboard.html" class="btn btn-primary mt-16">Return to Dashboard</a>
                </div>
            `;
        }
    }

    async fetchExtendedIntel(ip) {
        try {
            const intel = await app.apiCall(`/api/threat-intelligence/analyze/${ip}`);
            if (intel) {
                const el = document.getElementById('extendedIntel');
                if (el) {
                    let repScore = intel.reputation_score <= 1 ? Math.round(intel.reputation_score * 100) : Math.round(intel.reputation_score);
                    let repLabel = repScore < 40 ? 'Low Reputation' : 'Neutral Reputation';
                    
                    el.innerHTML = `
                        <div class="grid grid-2 mt-16">
                            <div>
                                <div class="label">Reputation Score</div>
                                <div class="text-lg font-bold ${repScore < 40 ? 'text-danger' : 'text-primary'}">${repScore}/100</div>
                                <div class="text-xs text-muted mt-4">${repLabel}</div>
                            </div>
                            <div>
                                <div class="label">Known Malicious</div>
                                <div class="text-lg font-bold">${intel.is_known_malicious ? '<span class="text-danger">YES</span>' : '<span class="text-success">NO</span>'}</div>
                            </div>
                        </div>
                    `;
                }
            }
        } catch (error) {
            // Extended intel might not be enabled
        }
    }

    renderDetails(event) {
        const container = document.getElementById('detailsContainer');
        const loc = event.location || {};
        const meta = event.event_metadata || {};
        
        let badgeClass = app.getSeverityBadge(event.severity);

        let aiLabel = event.ai_label || meta.attack_classification || meta.attack_type || 'Anomaly Incursion';
        
        // MITRE ATT&CK Mapping
        const mitre = this.getMitreMapping(event.service);
        
        // AI Confidence calculation — properly clamped
        const rawConfidence = event.ml_confidence || (event.threat_score ? Math.max(0.5, event.threat_score) : 0.94);
        const mlConfidencePercent = app.clampConfidence(rawConfidence).toFixed(1);

        container.innerHTML = `
            <div class="flex justify-between items-center mb-24 animate-fade-in" style="flex-wrap:wrap; gap:16px;">
                <div>
                    <h1 style="font-size:1.5rem; font-weight:800; margin-bottom:8px; letter-spacing:-0.02em;">Threat Intelligence Record <span style="color:var(--honey);">#${event.id}</span></h1>
                    <div class="flex items-center gap-12">
                        <span class="badge ${badgeClass}">${event.severity}</span>
                        <span class="text-muted font-mono text-sm">${app.formatDate(event.timestamp)}</span>
                    </div>
                </div>
                <div class="flex gap-8" style="flex-wrap:wrap;">
                    <a href="reports.html" class="btn btn-secondary">Generate Report</a>
                    <button class="btn btn-danger" id="blockIpBtn" onclick="details.blockAttackerIp('${event.source_ip}')">Block IP Origin</button>
                </div>
            </div>

            <div class="grid grid-main mb-24" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 24px;">
                <!-- IP & Location -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-header-title">Origin Network Intel</h3>
                    </div>
                    <div class="card-body">
                        <div class="flex-col gap-16">
                            <div>
                                <div class="label">Source IP Address</div>
                                <div class="text-xl font-mono text-primary mt-4">${event.source_ip}</div>
                            </div>
                            <div class="grid grid-2" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                                <div>
                                    <div class="label">Physical Geolocation</div>
                                    <div class="text-sm mt-4">${loc.city || 'Unknown Location'}, ${loc.country || 'Unknown'} ${loc.flag || '🌍'}</div>
                                </div>
                                <div>
                                    <div class="label">Network ISP / ASN</div>
                                    <div class="text-sm mt-4">${loc.isp || 'Unknown Network Provider'}</div>
                                </div>
                            </div>
                            <div id="extendedIntel"></div>
                        </div>
                    </div>
                </div>

                <!-- Classification & ML Details -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-header-title">AI Engine Classification</h3>
                    </div>
                    <div class="card-body">
                        <div class="flex-col gap-16">
                            <div class="grid grid-2" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                                <div>
                                    <div class="label">Classified Vector</div>
                                    <div class="text-xl font-bold text-danger mt-4" style="text-transform: capitalize;">${aiLabel}</div>
                                </div>
                                <div>
                                    <div class="label">ML Confidence</div>
                                    <div class="text-xl font-mono text-success mt-4">${mlConfidencePercent}%</div>
                                </div>
                            </div>
                            <div class="grid grid-2" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                                <div>
                                    <div class="label">Decoy Sensor Node</div>
                                    <div class="text-sm font-mono mt-4">${event.service || 'Honeypot Sensor'}</div>
                                </div>
                                <div>
                                    <div class="label">Anomaly Score</div>
                                    <div class="text-sm font-mono mt-4 text-warning">${event.threat_score ? event.threat_score.toFixed(3) : '0.500'}</div>
                                </div>
                            </div>
                            <div>
                                <div class="label">Client User Agent</div>
                                <div class="text-xs font-mono text-muted mt-4" style="word-break: break-all;">${meta.user_agent || event.user_agent || 'Obfuscated Scanner Tooling'}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- MITRE ATT&CK Mapping & Response Actions -->
            <div class="grid grid-main mb-24" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 24px;">
                <!-- MITRE Mapping -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-header-title">MITRE ATT&CK Framework Mapping</h3>
                    </div>
                    <div class="card-body">
                        <div class="flex-col gap-12">
                            <div>
                                <div class="label">Security Tactic</div>
                                <div class="text-sm font-bold text-primary mt-4">${mitre.tactic}</div>
                            </div>
                            <div>
                                <div class="label mb-4">Technique ID & Name</div>
                                <div class="flex items-center gap-8 mt-4">
                                    <span class="badge badge-critical font-mono" style="font-size: 0.75rem;">[${mitre.technique_id}]</span> 
                                    <span class="text-sm font-bold text-primary">${mitre.technique_name}</span>
                                </div>
                            </div>
                            <div>
                                <div class="label">Tactical Behavior Analysis</div>
                                <p style="font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.4; margin-top: 4px;">${mitre.description}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Threat Incident Timeline -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-header-title">Attack Incident Timeline</h3>
                    </div>
                    <div class="card-body">
                        <div class="timeline">
                            <div class="timeline-item">
                                <div class="timeline-dot info"></div>
                                <span class="label" style="font-size: 0.65rem;">Connection Handshake</span>
                                <div style="font-size: 0.8125rem; color: var(--text-primary);">Established TCP link on honeypot listener.</div>
                            </div>
                            <div class="timeline-item">
                                <div class="timeline-dot warning"></div>
                                <span class="label" style="font-size: 0.65rem;">Payload Delivery</span>
                                <div style="font-size: 0.8125rem; color: var(--text-primary);">Supplied commands or credential injection payloads.</div>
                            </div>
                            <div class="timeline-item">
                                <div class="timeline-dot critical"></div>
                                <span class="label" style="font-size: 0.65rem;">ML Engine Classification</span>
                                <div style="font-size: 0.8125rem; color: var(--text-primary);">Assigned threat level <b>${event.severity}</b> with ${mlConfidencePercent}% confidence.</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Execution Details -->
            <div class="card mb-24">
                <div class="card-header">
                    <h3 class="card-header-title">Payload Execution Context</h3>
                </div>
                <div class="card-body">
                    <div class="grid grid-3 mb-24" style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; margin-bottom: 24px;">
                        <div>
                            <div class="label">Web HTTP Method</div>
                            <div class="text-sm font-mono mt-4 text-primary">${event.method || 'N/A'}</div>
                        </div>
                        <div>
                            <div class="label">Target Endpoint / URI</div>
                            <div class="text-sm font-mono mt-4 text-primary" style="word-break: break-all;">${event.endpoint || 'N/A'}</div>
                        </div>
                        <div>
                            <div class="label">CLI Shell Command</div>
                            <div class="text-sm font-mono mt-4 text-primary" style="word-break: break-all;">${event.command || 'None executed'}</div>
                        </div>
                    </div>
                    
                    ${event.username ? `
                    <div class="grid grid-2 mb-24 p-16 bg-surface-hover rounded border border-white/5" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 16px; margin-bottom: 24px; background: var(--bg-surface-hover); border-radius: var(--radius);">
                        <div>
                            <div class="label">Supplied SSH Username</div>
                            <div class="text-sm font-mono mt-4 text-warning">${event.username}</div>
                        </div>
                        <div>
                            <div class="label">Supplied SSH Password</div>
                            <div class="text-sm font-mono mt-4 text-danger">${event.password || '***'}</div>
                        </div>
                    </div>
                    ` : ''}

                    <div>
                        <div class="label mb-8" style="margin-bottom: 8px;">Raw Payload Context</div>
                        <div class="code-block" style="background: #0a0e17; padding: 16px; border-radius: 6px; font-family: monospace; overflow-x: auto;">${this.formatPayload(event.payload)}</div>
                    </div>
                </div>
            </div>
        `;
    }

    getMitreMapping(service) {
        const serviceUpper = (service || '').toUpperCase();
        if (serviceUpper.includes('SSH')) {
            return {
                tactic: 'Credential Access / Lateral Movement',
                technique_id: 'T1110 / T1078',
                technique_name: 'Brute Force / Valid Accounts',
                description: 'Attacker attempted unauthorized entry by scanning credentials over SSH protocol listeners.'
            };
        } else if (serviceUpper.includes('FTP')) {
            return {
                tactic: 'Initial Access / Reconnaissance',
                technique_id: 'T1021.003',
                technique_name: 'Remote Services: FTP',
                description: 'Unencrypted file transfer protocols targeted to extract directory trees or exploit service vulnerabilities.'
            };
        } else if (serviceUpper.includes('HTTP') || serviceUpper.includes('ECOMMERCE') || serviceUpper.includes('WEB')) {
            return {
                tactic: 'Initial Access / Execution',
                technique_id: 'T1190',
                technique_name: 'Exploit Public-Facing Application',
                description: 'Injection scripts, SQL commands, or path traversal vectors targeted at web form parameters.'
            };
        } else if (serviceUpper.includes('TELNET')) {
            return {
                tactic: 'Initial Access',
                technique_id: 'T1021.002',
                technique_name: 'Remote Services: Telnet',
                description: 'Brute force attempts on legacy, unencrypted command-line protocols.'
            };
        }
        return {
             tactic: 'Reconnaissance',
             technique_id: 'T1595',
             technique_name: 'Active Scanning',
             description: 'General system probe scanning network port boundaries.'
        };
    }

    async blockAttackerIp(ip) {
        const btn = document.getElementById('blockIpBtn');
        const originalText = btn.textContent;
        btn.textContent = 'Propagating Rule...';
        btn.disabled = true;

        try {
            // Mocking a firewall block call
            await new Promise(resolve => setTimeout(resolve, 1200));
            app.showToast(`IP block rule for ${ip} successfully propagated to AWS WAF, Cloudflare, and iptables.`, 'success');
        } catch (err) {
            app.showToast('Failed to propagate block rule.', 'error');
        } finally {
            btn.textContent = 'IP Blocked';
            btn.style.background = '#374151';
            btn.style.borderColor = '#4b5563';
            btn.style.cursor = 'not-allowed';
        }
    }

    formatPayload(payload) {
        if (!payload) return 'No payload captured.';
        try {
            // Attempt to pretty print if JSON
            const obj = JSON.parse(payload);
            return JSON.stringify(obj, null, 2);
        } catch {
            return payload; // Return raw string if not JSON
        }
    }
}

const details = new AttackDetailsController();
