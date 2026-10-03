import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Search,
  Plus,
  Edit,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ShieldAlert,
  Loader2,
  X,
} from 'lucide-react';
import api from '../api/client';
import { SeverityBadge } from '../components/SeverityBadge';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { EmptyState } from '../components/EmptyState';
import { useToast } from '../context/ToastContext';

export const PolicyLibrary = () => {
  const [policies, setPolicies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [activeFilter, setActiveFilter] = useState('all');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [formData, setFormData] = useState({
    policy_code: '',
    section_number: '',
    title: '',
    category: '',
    description: '',
    severity_guidance: 'Medium',
    is_active: true,
  });
  const [modalLoading, setModalLoading] = useState(false);

  const toast = useToast();

  const fetchPolicies = async () => {
    try {
      setLoading(true);
      const res = await api.get('/api/policies');
      setPolicies(res.data.policies || []);
      setCategories(res.data.categories || []);
    } catch (err) {
      toast.error('Failed to load policy rules: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleOpenAdd = () => {
    setEditingPolicy(null);
    setFormData({
      policy_code: 'POL-NEW-001',
      section_number: 'Section 1.0',
      title: '',
      category: categories[0] || 'Product title guidelines',
      description: '',
      severity_guidance: 'Medium',
      is_active: true,
    });
    setIsModalOpen(true);
  };

  const handleOpenEdit = (policy) => {
    setEditingPolicy(policy);
    setFormData({
      policy_code: policy.policy_code,
      section_number: policy.section_number,
      title: policy.title,
      category: policy.category,
      description: policy.description,
      severity_guidance: policy.severity_guidance,
      is_active: policy.is_active,
    });
    setIsModalOpen(true);
  };

  const handleSavePolicy = async (e) => {
    e.preventDefault();
    setModalLoading(true);

    try {
      if (editingPolicy) {
        await api.put(`/api/policies/${editingPolicy.id}`, formData);
        toast.success(`Policy '${formData.policy_code}' updated successfully.`);
      } else {
        await api.post('/api/policies', formData);
        toast.success(`Policy '${formData.policy_code}' created successfully.`);
      }
      setIsModalOpen(false);
      fetchPolicies();
    } catch (err) {
      toast.error(err.message || 'Failed to save policy');
    } finally {
      setModalLoading(false);
    }
  };

  const handleToggleStatus = async (policy) => {
    try {
      const updated = !policy.is_active;
      await api.put(`/api/policies/${policy.id}`, { is_active: updated });
      toast.info(`Policy '${policy.policy_code}' ${updated ? 'enabled' : 'disabled'}.`);
      fetchPolicies();
    } catch (err) {
      toast.error('Failed to toggle status: ' + err.message);
    }
  };

  const handleDeletePolicy = async (policy) => {
    if (!window.confirm(`Are you sure you want to delete policy ${policy.policy_code}?`)) return;
    try {
      await api.delete(`/api/policies/${policy.id}`);
      toast.success(`Policy '${policy.policy_code}' deleted.`);
      fetchPolicies();
    } catch (err) {
      toast.error('Failed to delete policy: ' + err.message);
    }
  };

  const filtered = policies.filter((p) => {
    const matchesSearch =
      p.title.toLowerCase().includes(search.toLowerCase()) ||
      p.policy_code.toLowerCase().includes(search.toLowerCase()) ||
      p.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || p.category === selectedCategory;
    const matchesActive =
      activeFilter === 'all' ||
      (activeFilter === 'active' && p.is_active) ||
      (activeFilter === 'inactive' && !p.is_active);

    return matchesSearch && matchesCategory && matchesActive;
  });

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Marketplace Policy Library</h1>
          <p className="text-sm text-slate-500 mt-1">
            Rules, guidelines, and compliance standards referenced by the AI Reviewer.
          </p>
        </div>
        <button
          onClick={handleOpenAdd}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          Add Policy Rule
        </button>
      </div>

      {/* Mandatory Demonstration Notice Banner */}
      <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3 text-xs text-amber-900">
        <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Demonstration policy knowledge base:</span> Replace these sample
          rules with the official marketplace policy before production use.
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search code, title, or rule description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 text-slate-800 text-xs rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Policy Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <select
            value={activeFilter}
            onChange={(e) => setActiveFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
          </select>
        </div>
      </div>

      {/* Policy Cards Grid */}
      {loading ? (
        <LoadingSkeleton count={4} />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No policies found"
          description="Try adjusting your filter options or add a new policy rule."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((pol) => (
            <div
              key={pol.id}
              className={`bg-white rounded-2xl border p-5 shadow-2xs flex flex-col justify-between transition ${
                pol.is_active ? 'border-slate-200 hover:border-slate-300' : 'border-slate-200 opacity-60 bg-slate-50/50'
              }`}
            >
              <div className="space-y-3">
                {/* Header row */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-0.5 rounded">
                      {pol.policy_code}
                    </span>
                    <span className="text-[11px] font-semibold text-slate-500">
                      {pol.section_number}
                    </span>
                    {pol.is_demo_policy && (
                      <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.2 rounded font-medium">
                        Sample
                      </span>
                    )}
                  </div>
                  <SeverityBadge severity={pol.severity_guidance} />
                </div>

                {/* Title & Category */}
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{pol.title}</h3>
                  <span className="text-[11px] text-slate-400 font-medium">{pol.category}</span>
                </div>

                {/* Description */}
                <p className="text-xs text-slate-600 leading-relaxed bg-slate-50/75 p-3 rounded-xl border border-slate-100">
                  {pol.description}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                <button
                  type="button"
                  onClick={() => handleToggleStatus(pol)}
                  className={`inline-flex items-center gap-1 font-semibold ${
                    pol.is_active
                      ? 'text-emerald-700 hover:text-emerald-800'
                      : 'text-slate-400 hover:text-slate-600'
                  }`}
                >
                  {pol.is_active ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Active
                    </>
                  ) : (
                    <>
                      <XCircle className="w-3.5 h-3.5 text-slate-400" />
                      Inactive
                    </>
                  )}
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleOpenEdit(pol)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-50 transition"
                    title="Edit Rule"
                  >
                    <Edit className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDeletePolicy(pol)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition"
                    title="Delete Rule"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Policy Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-900">
                {editingPolicy ? `Edit Policy ${editingPolicy.policy_code}` : 'Add New Policy Rule'}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSavePolicy} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
                    Policy Code
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.policy_code}
                    onChange={(e) => setFormData({ ...formData, policy_code: e.target.value })}
                    placeholder="e.g. POL-TITLE-003"
                    className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
                    Section #
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.section_number}
                    onChange={(e) => setFormData({ ...formData, section_number: e.target.value })}
                    placeholder="e.g. Section 1.3"
                    className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
                  Policy Title
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g. Accurate Size and Fit Disclosure"
                  className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
                    Category
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="e.g. Product specifications"
                    className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
                    Severity Guidance
                  </label>
                  <select
                    value={formData.severity_guidance}
                    onChange={(e) => setFormData({ ...formData, severity_guidance: e.target.value })}
                    className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
                  Rule Description & Standards
                </label>
                <textarea
                  rows={4}
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe exact compliance expectations and prohibited practices..."
                  className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="active_checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="active_checkbox" className="text-xs text-slate-700 font-medium">
                  Enable policy rule immediately
                </label>
              </div>

              <div className="px-6 py-4 -mx-6 -mb-6 mt-6 border-t border-slate-100 flex items-center justify-end gap-3 bg-slate-50/50">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white transition shadow-sm disabled:opacity-50"
                >
                  {modalLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Save Policy'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
