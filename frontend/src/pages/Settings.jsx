import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Cpu,
  Database,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Sliders,
  ShieldAlert,
  Server,
  User,
} from 'lucide-react';
import api from '../api/client';
import { useToast } from '../context/ToastContext';

export const Settings = () => {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const res = await api.get('/api/health');
      setHealth(res.data);
    } catch (err) {
      toast.error('Health check failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System Settings & Health</h1>
          <p className="text-sm text-slate-500 mt-1">
            Environment configuration, AI model parameters, database connections, and reviewer profile.
          </p>
        </div>
        <button
          onClick={fetchHealth}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-2xs transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Diagnostics
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Gemini AI Engine Configuration */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">Google Gemini Integration</h2>
              <span className="text-xs text-slate-400">Gen AI Python SDK (google-genai)</span>
            </div>
          </div>

          <div className="space-y-3 text-xs pt-2">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Configured Model:</span>
              <span className="font-mono font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                {health?.gemini_model || 'gemini-2.5-flash'}
              </span>
            </div>

            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">API Key Configured:</span>
              <span
                className={`inline-flex items-center gap-1 font-semibold ${
                  health?.gemini_configured ? 'text-emerald-600' : 'text-amber-600'
                }`}
              >
                {health?.gemini_configured ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" /> Ready (Live Gemini API)
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-3.5 h-3.5" /> Pending in .env (Mock Mode Active)
                  </>
                )}
              </span>
            </div>

            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Structured Response Mode:</span>
              <span className="font-mono text-slate-800">application/json</span>
            </div>

            <div className="flex justify-between py-2">
              <span className="text-slate-500">Security Architecture:</span>
              <span className="text-emerald-700 font-semibold">Backend-only (No frontend key exposure)</span>
            </div>
          </div>
        </div>

        {/* Database Configuration */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">Database Engine</h2>
              <span className="text-xs text-slate-400">Flask-SQLAlchemy with MySQL & PyMySQL</span>
            </div>
          </div>

          <div className="space-y-3 text-xs pt-2">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Database Status:</span>
              <span
                className={`font-semibold inline-flex items-center gap-1 ${
                  health?.database === 'healthy' ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" /> {health?.database || 'Connected'}
              </span>
            </div>

            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Engine Type:</span>
              <span className="font-mono font-bold text-slate-800 uppercase">
                {health?.database_uri_type || 'MySQL'}
              </span>
            </div>

            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-500">Audit & Decision Trail:</span>
              <span className="font-semibold text-emerald-700">Persistent Database Records</span>
            </div>

            <div className="flex justify-between py-2">
              <span className="text-slate-500">Transaction Isolation:</span>
              <span className="text-slate-800 font-mono">ACID Compliant (db.session)</span>
            </div>
          </div>
        </div>

        {/* Deterministic Validation Engine Settings */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
              <Sliders className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">Deterministic Engine Parameters</h2>
              <span className="text-xs text-slate-400">Pre-AI Validation Rules</span>
            </div>
          </div>

          <div className="space-y-2 text-xs pt-2">
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Max Title Length:</span>
              <span className="font-mono font-semibold text-slate-800">150 characters</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Min Title Length:</span>
              <span className="font-mono font-semibold text-slate-800">5 characters</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Max Description Length:</span>
              <span className="font-mono font-semibold text-slate-800">5000 characters</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Min Description Length:</span>
              <span className="font-mono font-semibold text-slate-800">20 characters</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500">Duplicate Check Algorithm:</span>
              <span className="text-slate-800 font-semibold">Normalized Title & Jaccard Token Overlap</span>
            </div>
          </div>
        </div>

        {/* Current Reviewer Profile */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600">
              <User className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">Reviewer Session Profile</h2>
              <span className="text-xs text-slate-400">Role & Audit Assignment</span>
            </div>
          </div>

          <div className="space-y-2 text-xs pt-2">
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Reviewer Name:</span>
              <span className="font-semibold text-slate-800">Suhas</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Email:</span>
              <span className="font-mono text-slate-600">compliance@marketplace.local</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Assigned Role:</span>
              <span className="font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                Senior Reviewer & Compliance Officer
              </span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500">Human Approval Privilege:</span>
              <span className="text-emerald-700 font-semibold">Full Approval & Edit Authorization</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
