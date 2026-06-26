import React, { useState, useEffect } from 'react';
import { Trash2, RotateCcw, AlertOctagon, CheckSquare, Square, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

const RecycleBin = () => {
  const { apiCall } = useAuth();
  const { showToast } = useToast();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItems, setSelectedItems] = useState([]); // Array of { id, type }

  const loadItems = async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/recycle-bin');
      setItems(data);
      setSelectedItems([]);
    } catch (err) {
      showToast('Failed to retrieve deleted events', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadItems();
  }, []);

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedItems(items.map((item) => ({ id: item.id, type: item.type })));
    } else {
      setSelectedItems([]);
    }
  };

  const handleSelectItem = (id, type, checked) => {
    if (checked) {
      setSelectedItems((prev) => [...prev, { id, type }]);
    } else {
      setSelectedItems((prev) => prev.filter((item) => !(item.id === id && item.type === type)));
    }
  };

  const isSelected = (id, type) => {
    return selectedItems.some((item) => item.id === id && item.type === type);
  };

  const handleRestore = async (id, type) => {
    try {
      await apiCall('/api/recycle-bin/restore', {
        method: 'POST',
        body: JSON.stringify({ ids: [id], type })
      });
      showToast('Event telemetry restored successfully.', 'success');
      await loadItems();
    } catch (err) {
      showToast('Failed to restore event logs.', 'error');
    }
  };

  const handleDelete = async (id, type) => {
    try {
      await apiCall('/api/recycle-bin/permanent', {
        method: 'DELETE',
        body: JSON.stringify({ ids: [id], type })
      });
      showToast('Record purged permanently.', 'success');
      await loadItems();
    } catch (err) {
      showToast('Purging record failed.', 'error');
    }
  };

  const handleRestoreAll = async () => {
    try {
      await apiCall('/api/recycle-bin/restore', {
        method: 'POST',
        body: JSON.stringify({})
      });
      showToast('All events restored successfully.', 'success');
      await loadItems();
    } catch (err) {
      showToast('Failed to restore all logs.', 'error');
    }
  };

  const handleEmptyBin = async () => {
    try {
      await apiCall('/api/recycle-bin/permanent', {
        method: 'DELETE',
        body: JSON.stringify({})
      });
      showToast('Recycle bin emptied.', 'success');
      await loadItems();
    } catch (err) {
      showToast('Failed to empty bin.', 'error');
    }
  };

  const handleRestoreSelected = async () => {
    if (selectedItems.length === 0) return;
    try {
      // Group by type
      const grouped = selectedItems.reduce((acc, item) => {
        if (!acc[item.type]) acc[item.type] = [];
        acc[item.type].push(parseInt(item.id));
        return acc;
      }, {});

      for (const [type, ids] of Object.entries(grouped)) {
        await apiCall('/api/recycle-bin/restore', {
          method: 'POST',
          body: JSON.stringify({ ids, type })
        });
      }
      showToast('Selected events restored successfully.', 'success');
      await loadItems();
    } catch (err) {
      showToast('Failed to restore selected items.', 'error');
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedItems.length === 0) return;
    try {
      // Group by type
      const grouped = selectedItems.reduce((acc, item) => {
        if (!acc[item.type]) acc[item.type] = [];
        acc[item.type].push(parseInt(item.id));
        return acc;
      }, {});

      for (const [type, ids] of Object.entries(grouped)) {
        await apiCall('/api/recycle-bin/permanent', {
          method: 'DELETE',
          body: JSON.stringify({ ids, type })
        });
      }
      showToast('Selected records purged permanently.', 'success');
      await loadItems();
    } catch (err) {
      showToast('Failed to purge selected items.', 'error');
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh]">
        <RefreshCw className="animate-spin text-amber-500 mb-4" size={32} />
        <span className="text-sm text-slate-400 font-mono">Loading data lifecycle status...</span>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 flex flex-col gap-6">
      
      {/* Title */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-slate-100 text-lg font-bold">Data Lifecycle Management</h2>
          <p className="text-slate-400 text-xs">
            Review soft-deleted threat analytics logs. Restore accidental deletions or purge databases.
          </p>
        </div>
        {selectedItems.length === 0 && (
          <div className="flex gap-2">
            <button
              onClick={handleRestoreAll}
              disabled={items.length === 0}
              className="bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 px-3.5 py-1.8 rounded-lg text-xs font-semibold flex items-center gap-1.5 cursor-pointer disabled:opacity-40"
            >
              <RotateCcw size={13} />
              Restore All
            </button>
            <button
              onClick={handleEmptyBin}
              disabled={items.length === 0}
              className="bg-rose-500/10 hover:bg-rose-500 text-rose-500 hover:text-slate-950 border border-rose-500/20 px-3.5 py-1.8 rounded-lg text-xs font-semibold flex items-center gap-1.5 cursor-pointer disabled:opacity-40"
            >
              <AlertOctagon size={13} />
              Empty Recycle Bin
            </button>
          </div>
        )}
      </div>

      {/* Selected Items Bulk Actions Banner */}
      {selectedItems.length > 0 && (
        <div className="bg-slate-900 border border-amber-500/30 px-5 py-3 rounded-xl flex items-center justify-between animate-fade-in shadow-lg">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
            <span className="text-slate-200 text-xs font-semibold">
              <span className="font-mono text-amber-500 font-extrabold">{selectedItems.length}</span> items selected
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleRestoreSelected}
              className="bg-emerald-500/10 hover:bg-emerald-500 text-emerald-500 hover:text-slate-950 border border-emerald-500/20 px-3 py-1.5 rounded-lg text-xxs font-bold uppercase cursor-pointer"
            >
              Restore Selected
            </button>
            <button
              onClick={handleDeleteSelected}
              className="bg-rose-500/10 hover:bg-rose-500 text-rose-500 hover:text-slate-950 border border-rose-500/20 px-3 py-1.5 rounded-lg text-xxs font-bold uppercase cursor-pointer"
            >
              Purge Selected
            </button>
          </div>
        </div>
      )}

      {/* Content Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="overflow-x-auto w-full">
          <table className="w-full text-left text-xs text-slate-400 font-mono">
            <thead>
              <tr className="border-b border-slate-850 text-slate-500">
                <th className="py-2.5 px-3 w-10">
                  <input
                    type="checkbox"
                    checked={items.length > 0 && selectedItems.length === items.length}
                    onChange={handleSelectAll}
                    disabled={items.length === 0}
                    className="w-4 h-4 rounded border-slate-800 bg-slate-950 text-amber-500 focus:ring-amber-500/30 cursor-pointer"
                  />
                </th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Event Summary</th>
                <th className="py-2.5 px-3">Deleted Date</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-850">
              {items.length === 0 ? (
                <tr>
                  <td colSpan="5" className="py-10 text-center text-slate-500">Recycle Bin is empty</td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id + item.type} className="hover:bg-slate-850/20 transition-colors">
                    <td className="py-2.5 px-3 w-10">
                      <input
                        type="checkbox"
                        checked={isSelected(item.id, item.type)}
                        onChange={(e) => handleSelectItem(item.id, item.type, e.target.checked)}
                        className="w-4 h-4 rounded border-slate-800 bg-slate-950 text-amber-500 focus:ring-amber-500/30 cursor-pointer"
                      />
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded text-xxs font-bold uppercase tracking-wider bg-slate-800 border border-slate-700 text-slate-400">
                        {item.type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-200 font-semibold">{item.name}</td>
                    <td className="py-2.5 px-3 text-slate-500">{item.deleted_at ? new Date(item.deleted_at.includes('+') || item.deleted_at.endsWith('Z') ? item.deleted_at : item.deleted_at + 'Z').toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}</td>
                    <td className="py-2.5 px-3 text-right flex justify-end gap-2">
                      <button
                        onClick={() => handleRestore(item.id, item.type)}
                        className="bg-slate-800 hover:bg-emerald-500/10 text-slate-350 hover:text-emerald-500 border border-slate-700 hover:border-emerald-500/20 px-2 py-1 rounded text-xxs cursor-pointer"
                      >
                        Restore
                      </button>
                      <button
                        onClick={() => handleDelete(item.id, item.type)}
                        className="bg-slate-800 hover:bg-rose-500/10 text-slate-350 hover:text-rose-500 border border-slate-700 hover:border-rose-500/20 px-2 py-1 rounded text-xxs cursor-pointer"
                      >
                        Purge
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};

export default RecycleBin;
