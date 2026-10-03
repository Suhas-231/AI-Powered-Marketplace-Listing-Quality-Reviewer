import React, { useState, useEffect } from 'react';
import {
  History,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Edit,
  Sparkles,
  Package,
  BookOpen,
  ArrowRight,
  User,
} from 'lucide-react';
import api from '../api/client';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { EmptyState } from '../components/EmptyState';
import { useToast } from '../context/ToastContext';

export const ReviewHistory = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [entityType, setEntityType] = useState('all');
  const [search, setSearch] = useState('');
  const toast = useToast();

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const params = {
        entity_type: entityType !== 'all' ? entityType : undefined,
        per_page: 50,
      };
      const res = await api.get('/api/history', { params });
      setLogs(res.data.logs || []);
    } catch (err) {
      toast.error('Failed to load audit history: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [entityType]);

  const filteredLogs = logs.filter((l) => {
    const s = search.toLowerCase();
    return (
      l.action.toLowerCase().includes(s) ||
      l.entity_type.toLowerCase().includes(s) ||
      (l.user_name || '').toLowerCase().includes(s) ||
      JSON.stringify(l.details || {}).toLowerCase().includes(s)
    );
  });

  const getActionBadge = (action) => {
    const act = (action || '').toLowerCase();
    if (act.includes('approve')) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-bold uppercase bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded">
          <CheckCircle2 className="w-3 h-3" /> Approved
        </span>
      );
    }
    if (act.includes('reject')) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-bold uppercase bg-rose-100 text-rose-800 px-2 py-0.5 rounded">
          <XCircle className="w-3 h-3" /> Rejected
        </span>
      );
    }
    if (act.includes('edit')) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-bold uppercase bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded">
          <Edit className="w-3 h-3" /> Edited
        </span>
      );
    }
    if (act.includes('completed') || act.includes('review')) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-bold uppercase bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
          <Sparkles className="w-3 h-3" /> AI Reviewed
        </span>
      );
    }
    return (
      <span className="inline-flex items-center text-[11px] font-bold uppercase bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
        {action}
      </span>
    );
  };

  const getEntityIcon = (entity) => {
    switch (entity) {
      case 'listing':
        return <Package className="w-4 h-4 text-slate-500" />;
      case 'review':
        return <Sparkles className="w-4 h-4 text-indigo-500" />;
      case 'policy':
        return <BookOpen className="w-4 h-4 text-amber-500" />;
      default:
        return <History className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System Audit & Review History</h1>
          <p className="text-sm text-slate-500 mt-1">
            Complete persistent audit trail of AI reviews, human approval actions, and listing modifications.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search action, details, user..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 text-slate-800 text-xs rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Entity Types</option>
            <option value="listing">Listings</option>
            <option value="review">Reviews</option>
            <option value="suggestion">Suggestions (Decisions)</option>
            <option value="policy">Policies</option>
            <option value="batch">Batch Operations</option>
          </select>
        </div>
      </div>

      {/* Audit Log Timeline / Table */}
      {loading ? (
        <LoadingSkeleton count={5} />
      ) : filteredLogs.length === 0 ? (
        <EmptyState
          title="No history records found"
          description="Actions performed across the application will be recorded here automatically."
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Entity</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Audit Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3.5 px-4 text-slate-500 whitespace-nowrap font-mono text-[11px]">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <div className="flex items-center gap-1.5 font-semibold text-slate-800 capitalize">
                      {getEntityIcon(log.entity_type)}
                      <span>
                        {log.entity_type} #{log.entity_id}
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    {getActionBadge(log.action)}
                  </td>
                  <td className="py-3.5 px-4 whitespace-nowrap text-slate-600">
                    <span className="inline-flex items-center gap-1">
                      <User className="w-3 h-3 text-slate-400" />
                      {log.user_name || 'System'}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 max-w-md">
                    <span className="font-mono text-[11px] bg-slate-50 p-1.5 rounded border border-slate-100 block break-words">
                      {JSON.stringify(log.details)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
