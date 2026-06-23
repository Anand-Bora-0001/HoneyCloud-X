/**
 * Investigations Controller
 */
class InvestigationsController {
    constructor() {
        if (!app.isAuthenticated()) {
            app.logout();
            return;
        }
        this.investigations = [];
        this.init();
    }

    async init() {
        app.injectTopbar('Adversary Investigations', { showSearch: false });
        await this.loadInvestigations();
    }

    async loadInvestigations() {
        app.showLoadingSkeleton('investigationsContainer', 'cards', 3);
        try {
            const list = await app.apiCall('/api/investigations/');
            this.investigations = list;

            if (list.length === 0) {
                document.getElementById('emptyState').classList.remove('hidden');
                document.getElementById('emptyState').style.display = 'flex';
                document.getElementById('investigationsContainer').innerHTML = '';
                return;
            }

            document.getElementById('emptyState').classList.add('hidden');
            document.getElementById('emptyState').style.display = 'none';

            this.renderInvestigations();
        } catch (error) {
            app.showToast(error.message, 'error');
            document.getElementById('investigationsContainer').innerHTML = `
                <div class="p-16 text-center text-danger">Failed to load investigations: ${error.message}</div>
            `;
        }
    }

    renderInvestigations() {
        const container = document.getElementById('investigationsContainer');
        container.innerHTML = this.investigations.map(inv => {
            let summaryText = inv.summary || '';
            let ip = 'Unknown Attacker';
            let persona = 'APT Threat Group';

            const match = summaryText.match(/Profile ([\d\.]+) is classified as ([\w\s]+) with/);
            if (match) {
                ip = match[1];
                persona = match[2];
                summaryText = `The actor at <b>${ip}</b> performed anomalous behavior patterns consistent with a <b>${persona}</b> profile. Behavior indicates targeted activity requiring immediate SOC review.`;
            }

            return `
                <div class="card border-warning shadow-md mb-16" id="inv-card-${inv.attacker_id}">
                    <div class="card-header flex justify-between items-center" style="cursor:pointer;" onclick="investigations.toggleDetail(${inv.attacker_id})">
                        <div class="flex items-center gap-12">
                            <span class="text-xl">🕵️‍♂️</span>
                            <div class="flex-col">
                                <h4 class="card-header-title text-accent">Report #${inv.attacker_id} — ${ip}</h4>
                                <span class="text-xs text-muted">Updated: ${app.formatRelativeTime(inv.updated_at)}</span>
                            </div>
                        </div>
                        <div class="flex items-center gap-12">
                            <span class="badge badge-warning">${persona}</span>
                            <button class="btn btn-secondary btn-sm" id="btn-toggle-${inv.attacker_id}">Inspect ▾</button>
                        </div>
                    </div>
                    <div class="card-body">
                        <p class="text-sm text-secondary mb-16 leading-relaxed">${summaryText}</p>
                        
                        <div id="detail-${inv.attacker_id}" class="hidden mt-16 pt-16 border-t border-white/5 flex-col gap-16" style="display: none;">
                            <!-- Detail content will load dynamically when expanded -->
                            <div class="flex items-center justify-center p-24">
                                <span class="animate-spin" style="display:inline-block;width:18px;height:18px;border:2px solid var(--border);border-top-color:var(--honey);border-radius:50%;"></span>
                                <span class="text-xs text-muted ml-8">Analyzing telemetry...</span>
                            </div>
                        </div>
                        
                        <div class="flex items-center gap-12 mt-16">
                            <a href="${app.apiBase}/api/investigations/${inv.attacker_id}/report?format=csv" target="_blank" class="btn btn-secondary btn-sm flex items-center gap-4">
                                📥 Export CSV
                            </a>
                            <a href="${app.apiBase}/api/investigations/${inv.attacker_id}/report?format=json" target="_blank" class="btn btn-secondary btn-sm flex items-center gap-4">
                                📥 Export JSON
                            </a>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async toggleDetail(profileId) {
        const detailEl = document.getElementById(`detail-${profileId}`);
        const btn = document.getElementById(`btn-toggle-${profileId}`);
        if (!detailEl) return;

        const isOpen = !detailEl.classList.contains('hidden');
        if (isOpen) {
            detailEl.classList.add('hidden');
            detailEl.style.display = 'none';
            btn.textContent = 'Inspect ▾';
        } else {
            detailEl.classList.remove('hidden');
            detailEl.style.display = 'flex';
            btn.textContent = 'Collapse ▴';
            
            // Load detail content if not already loaded
            if (detailEl.dataset.loaded !== 'true') {
                try {
                    const data = await app.apiCall(`/api/investigations/${profileId}`);
                    if (data.status === 'ready') {
                        let mitreHtml = 'No MITRE mapping found.';
                        if (data.mitre_mapping && Object.keys(data.mitre_mapping).length > 0) {
                            mitreHtml = Object.entries(data.mitre_mapping).map(([id, desc]) => `
                                <div class="p-8 bg-black/10 rounded border border-white/5 mb-4">
                                    <span class="font-mono text-accent font-bold">${id}</span> — <span class="text-xs text-secondary">${desc}</span>
                                </div>
                            `).join('');
                        }

                        let attackPathsHtml = 'No paths detected.';
                        if (data.attack_paths && data.attack_paths.length > 0) {
                            attackPathsHtml = data.attack_paths.map(p => `
                                <div class="text-xs font-mono text-success mb-2">● ${p}</div>
                            `).join('');
                        }

                        detailEl.innerHTML = `
                            <div class="grid grid-2 gap-16 w-full">
                                <div>
                                    <h4 class="text-xs label mb-8">Executive Narrative</h4>
                                    <p class="text-sm text-secondary leading-relaxed mb-16">${data.executive || 'N/A'}</p>
                                    
                                    <h4 class="text-xs label mb-8">Technical Impact</h4>
                                    <p class="text-sm text-secondary leading-relaxed">${data.technical || 'N/A'}</p>
                                </div>
                                <div>
                                    <h4 class="text-xs label mb-8">MITRE ATT&CK Mapping</h4>
                                    <div class="flex-col gap-8 mb-16">${mitreHtml}</div>

                                    <h4 class="text-xs label mb-8">Attack Paths</h4>
                                    <div class="flex-col gap-4">${attackPathsHtml}</div>
                                </div>
                            </div>
                            
                            ${data.evidence ? `
                            <div class="mt-8 w-full">
                                <h4 class="text-xs label mb-8">Evidence Telemetry</h4>
                                <pre class="code-block" style="white-space: pre-wrap; font-size: 0.7rem; overflow-x: auto;">${data.evidence}</pre>
                            </div>
                            ` : ''}
                        `;
                        detailEl.dataset.loaded = 'true';
                    } else {
                        detailEl.innerHTML = `<div class="p-16 text-xs text-muted">${data.message || 'Investigation report is compiling...'}</div>`;
                    }
                } catch (err) {
                    detailEl.innerHTML = `<div class="p-16 text-xs text-danger">Failed to fetch report detail: ${err.message}</div>`;
                }
            }
        }
    }
}

// Start
window.investigations = new InvestigationsController();
