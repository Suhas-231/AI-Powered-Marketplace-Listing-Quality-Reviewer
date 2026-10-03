import React, { useState, useEffect } from 'react';
import {
  X,
  User,
  Mail,
  Shield,
  Hash,
  Calendar,
  Edit3,
  Check,
  Loader2,
  Lock,
  AlertCircle,
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import { useToast } from '../context/ToastContext';

export const ProfileModal = ({ isOpen, onClose, initialMode = 'view' }) => {
  const { user, updateProfile } = useUser();
  const toast = useToast();

  const [mode, setMode] = useState(initialMode); // 'view' or 'edit'
  const [formData, setFormData] = useState({ name: '', email: '' });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setMode(initialMode);
      if (user) {
        setFormData({
          name: user.name || '',
          email: user.email || '',
        });
      }
      setErrors({});
    }
  }, [isOpen, initialMode, user]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && !saving) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, saving, onClose]);

  if (!isOpen || !user) return null;

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Full name is required.';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'Full name must be at least 2 characters.';
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email.trim()) {
      newErrors.email = 'Email address is required.';
    } else if (!emailRegex.test(formData.email.trim())) {
      newErrors.email = 'Please enter a valid email address.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      setSaving(true);
      await updateProfile({
        name: formData.name.trim(),
        email: formData.email.trim(),
      });
      toast.success('User profile updated successfully!');
      setMode('view');
    } catch (err) {
      const errMsg = err.response?.data?.message || err.message || 'Failed to update profile';
      toast.error(errMsg);
      if (errMsg.toLowerCase().includes('email')) {
        setErrors((prev) => ({ ...prev, email: errMsg }));
      }
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      name: user.name || '',
      email: user.email || '',
    });
    setErrors({});
    setMode('view');
  };

  const formattedDate = user.created_at
    ? new Date(user.created_at).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'System Initialized';

  const userInitial = (user.name || 'U').charAt(0).toUpperCase();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs transition-opacity"
      onClick={(e) => {
        if (e.target === e.currentTarget && !saving) {
          onClose();
        }
      }}
    >
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <User className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                {mode === 'edit' ? 'Edit User Profile' : 'User Profile Details'}
              </h3>
              <p className="text-xs text-slate-500">
                {mode === 'edit'
                  ? 'Update your full name and primary email address.'
                  : 'Manage reviewer identity and account credentials.'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={saving}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* User Identity Banner */}
        <div className="px-6 pt-5 pb-3 flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-indigo-600 text-white flex items-center justify-center text-xl font-bold shadow-md shadow-indigo-600/20 flex-shrink-0">
            {userInitial}
          </div>
          <div className="min-w-0 flex-1">
            <h4 className="text-base font-bold text-slate-900 truncate">{user.name}</h4>
            <p className="text-xs text-slate-500 truncate">{user.email}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                <Shield className="w-3 h-3" />
                {user.role}
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] text-slate-400 font-mono">
                <Hash className="w-3 h-3" />
                ID #{user.id}
              </span>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="px-6 py-4">
          {mode === 'view' ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {/* Full Name */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Full Name
                  </span>
                  <span className="font-semibold text-slate-900 text-sm block truncate">
                    {user.name}
                  </span>
                </div>

                {/* Email Address */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Email Address
                  </span>
                  <span className="font-semibold text-slate-900 text-sm block truncate">
                    {user.email}
                  </span>
                </div>

                {/* Role (Read-only) */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Assigned Role
                    </span>
                    <span className="text-[10px] text-slate-400 flex items-center gap-0.5 font-medium">
                      <Lock className="w-2.5 h-2.5" /> Read-only
                    </span>
                  </div>
                  <span className="font-semibold text-slate-800 text-sm block">
                    {user.role}
                  </span>
                </div>

                {/* Account ID (Read-only) */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Account ID
                    </span>
                    <span className="text-[10px] text-slate-400 flex items-center gap-0.5 font-medium">
                      <Lock className="w-2.5 h-2.5" /> Read-only
                    </span>
                  </div>
                  <span className="font-mono font-bold text-slate-800 text-sm block">
                    #{user.id}
                  </span>
                </div>
              </div>

              {/* Registration Date */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-500 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" /> Member Since:
                </span>
                <span className="font-semibold text-slate-700">{formattedDate}</span>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSave} className="space-y-4">
              {/* Full Name Input */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Full Name <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => {
                      setFormData({ ...formData, name: e.target.value });
                      if (errors.name) setErrors({ ...errors, name: null });
                    }}
                    placeholder="Enter your full name"
                    className={`w-full bg-slate-50 border ${
                      errors.name ? 'border-rose-400 focus:ring-rose-200' : 'border-slate-200 focus:ring-indigo-200'
                    } text-slate-900 text-xs rounded-xl pl-9 pr-3.5 py-2.5 focus:outline-none focus:ring-2 focus:border-indigo-500 transition`}
                  />
                </div>
                {errors.name && (
                  <p className="text-[11px] text-rose-600 mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.name}
                  </p>
                )}
              </div>

              {/* Email Input */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Email Address <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => {
                      setFormData({ ...formData, email: e.target.value });
                      if (errors.email) setErrors({ ...errors, email: null });
                    }}
                    placeholder="Enter your email address"
                    className={`w-full bg-slate-50 border ${
                      errors.email ? 'border-rose-400 focus:ring-rose-200' : 'border-slate-200 focus:ring-indigo-200'
                    } text-slate-900 text-xs rounded-xl pl-9 pr-3.5 py-2.5 focus:outline-none focus:ring-2 focus:border-indigo-500 transition`}
                  />
                </div>
                {errors.email && (
                  <p className="text-[11px] text-rose-600 mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.email}
                  </p>
                )}
              </div>

              {/* Read-only System Fields */}
              <div className="grid grid-cols-2 gap-3 pt-1">
                <div className="p-2.5 bg-slate-50/70 rounded-xl border border-slate-200/60 text-xs">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold flex items-center gap-1 mb-0.5">
                    <Lock className="w-2.5 h-2.5" /> Role (Locked)
                  </span>
                  <span className="font-semibold text-slate-700 block truncate">{user.role}</span>
                </div>
                <div className="p-2.5 bg-slate-50/70 rounded-xl border border-slate-200/60 text-xs">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold flex items-center gap-1 mb-0.5">
                    <Lock className="w-2.5 h-2.5" /> Account ID
                  </span>
                  <span className="font-mono font-semibold text-slate-700 block">#{user.id}</span>
                </div>
              </div>
            </form>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 bg-slate-50/60 border-t border-slate-100 flex items-center justify-end gap-2.5">
          {mode === 'view' ? (
            <>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 transition"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => setMode('edit')}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition"
              >
                <Edit3 className="w-3.5 h-3.5" />
                Edit Profile
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={handleCancel}
                disabled={saving}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition disabled:opacity-60"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Saving Changes...
                  </>
                ) : (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    Save Changes
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
