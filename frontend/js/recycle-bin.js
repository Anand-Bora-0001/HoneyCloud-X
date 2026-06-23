/**
 * Recycle Bin Controller
 */
class RecycleBinController {
    constructor() {
        if (!app.isAuthenticated()) {
            app.logout();
            return;
        }
        
        this.items = [];
        this.selectedIds = new Set();
        
        this.init();
    }

    async init() {
        app.injectTopbar('Data Lifecycle Management', { showSearch: false });
        await this.loadItems();
        this.setupListeners();
    }

    async loadItems() {
        try {
            this.items = await app.apiCall('/api/recycle-bin');
            this.renderItems();
        } catch (e) {
            app.showToast('Failed to load recycle bin items', 'error');
            const tbody = document.getElementById('binBody');
            if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="text-center p-24 text-danger">Error loading data</td></tr>`;
        }
    }

    renderItems() {
        const tbody = document.getElementById('binBody');
        if (!tbody) return;

        if (this.items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center p-24 text-muted">Recycle Bin is empty</td></tr>`;
            document.getElementById('bulkActionsBanner').style.display = 'none';
            return;
        }

        tbody.innerHTML = this.items.map(item => `
            <tr>
                <td><input type="checkbox" class="item-checkbox w-4 h-4" data-id="${item.id}" data-type="${item.type}"></td>
                <td><span class="badge badge-low">${item.type}</span></td>
                <td class="font-bold">${item.name}</td>
                <td class="font-mono text-muted text-sm">${app.formatDate(item.deleted_at)}</td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="recycleBin.restoreItem(${item.id}, '${item.type}')">Restore</button>
                    <button class="btn btn-danger btn-sm" onclick="recycleBin.deleteItem(${item.id}, '${item.type}')">Delete</button>
                </td>
            </tr>
        `).join('');
        
        this.updateSelection();
    }

    setupListeners() {
        const selectAll = document.getElementById('selectAllBin');
        if (selectAll) {
            selectAll.addEventListener('change', (e) => {
                const checkboxes = document.querySelectorAll('.item-checkbox');
                this.selectedIds.clear();
                
                checkboxes.forEach(cb => {
                    cb.checked = e.target.checked;
                    if (cb.checked) {
                        this.selectedIds.add({ id: cb.dataset.id, type: cb.dataset.type });
                    }
                });
                
                this.updateSelection();
            });
        }
        
        document.getElementById('binBody').addEventListener('change', (e) => {
            if (e.target.classList.contains('item-checkbox')) {
                const item = { id: e.target.dataset.id, type: e.target.dataset.type };
                if (e.target.checked) {
                    this.selectedIds.add(item);
                } else {
                    // Custom delete from set by checking id and type
                    for (let s of this.selectedIds) {
                        if (s.id == item.id && s.type == item.type) {
                            this.selectedIds.delete(s);
                            break;
                        }
                    }
                }
                this.updateSelection();
            }
        });
    }

    updateSelection() {
        const banner = document.getElementById('bulkActionsBanner');
        const count = document.getElementById('selectedCount');
        
        if (this.selectedIds.size > 0) {
            banner.style.display = 'flex';
            count.textContent = this.selectedIds.size;
        } else {
            banner.style.display = 'none';
        }
    }

    // --- Actions ---

    async restoreItem(id, type) {
        try {
            await app.apiCall('/api/recycle-bin/restore', {
                method: 'POST',
                body: JSON.stringify({ ids: [id], type: type })
            });
            app.showToast('Item restored successfully', 'success');
            await this.loadItems();
        } catch (e) {
            app.showToast('Failed to restore item', 'error');
        }
    }
    
    async deleteItem(id, type) {
        if (!confirm('Permanently delete this item? This action cannot be undone.')) return;
        try {
            await app.apiCall('/api/recycle-bin/permanent', {
                method: 'DELETE',
                body: JSON.stringify({ ids: [id], type: type })
            });
            app.showToast('Item permanently deleted', 'success');
            await this.loadItems();
        } catch (e) {
            app.showToast('Failed to delete item', 'error');
        }
    }

    async emptyBin() {
        if (!confirm('Are you absolutely sure you want to permanently delete all items in the Recycle Bin?')) return;
        try {
            await app.apiCall('/api/recycle-bin/permanent', {
                method: 'DELETE',
                body: JSON.stringify({})
            });
            app.showToast('Recycle bin emptied', 'success');
            await this.loadItems();
        } catch (e) {
            app.showToast('Failed to empty recycle bin', 'error');
        }
    }
    
    async restoreAll() {
        try {
            await app.apiCall('/api/recycle-bin/restore', {
                method: 'POST',
                body: JSON.stringify({})
            });
            app.showToast('All items restored successfully', 'success');
            await this.loadItems();
        } catch (e) {
            app.showToast('Failed to restore items', 'error');
        }
    }
    
    async restoreSelected() {
        if (this.selectedIds.size === 0) return;
        try {
            // Group by type
            let idsByType = {};
            for (let s of this.selectedIds) {
                if (!idsByType[s.type]) idsByType[s.type] = [];
                idsByType[s.type].push(parseInt(s.id));
            }
            
            for (let type in idsByType) {
                await app.apiCall('/api/recycle-bin/restore', {
                    method: 'POST',
                    body: JSON.stringify({ ids: idsByType[type], type: type })
                });
            }
            
            app.showToast('Selected items restored', 'success');
            this.selectedIds.clear();
            await this.loadItems();
        } catch (e) {
            app.showToast('Failed to restore selected items', 'error');
        }
    }

    async deleteSelected() {
        if (this.selectedIds.size === 0) return;
        if (!confirm(`Permanently delete ${this.selectedIds.size} selected items?`)) return;
        try {
            let idsByType = {};
            for (let s of this.selectedIds) {
                if (!idsByType[s.type]) idsByType[s.type] = [];
                idsByType[s.type].push(parseInt(s.id));
            }
            
            for (let type in idsByType) {
                await app.apiCall('/api/recycle-bin/permanent', {
                    method: 'DELETE',
                    body: JSON.stringify({ ids: idsByType[type], type: type })
                });
            }
            
            app.showToast('Selected items permanently deleted', 'success');
            this.selectedIds.clear();
            await this.loadItems();
        } catch (e) {
            app.showToast('Failed to delete selected items', 'error');
        }
    }
}

const recycleBin = new RecycleBinController();
