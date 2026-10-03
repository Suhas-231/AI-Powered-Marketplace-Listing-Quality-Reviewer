import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Package,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  PlusCircle,
  Sparkles,
  BookOpen,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';
import api from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { SeverityBadge } from '../components/SeverityBadge';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { EmptyState } from '../components/EmptyState';
import { useToast } from '../context/ToastContext';

export const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await api.get('/api/dashboard/stats');
      setStats(res.data);
    } catch (err) {
      toast.error('Failed to load dashboard metrics: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="p-8 space-y-6 max-w-7xl mx-auto">
        <div className="h-8 bg-slate-200 rounded w-48 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-28 bg-white rounded-xl border border-slate-200 animate-pulse p-4" />
          ))}
        </div>
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  const summary = stats?.summary || {
    total_listings: 0,
    pending_reviews: 0,
    approved_revisions: 0,
    rejected_revisions: 0,
    listings_requiring_attention: 0,
  };

  const cards = [
    {
      title: 'Total Listings',
      value: summary.total_listings,
      icon: Package,
      color: 'text-indigo-600 bg-indigo-50 border-indigo-100',
    },
    {
      title: 'Pending Reviews',
      value: summary.pending_reviews,
      icon: Clock,
      color: 'text-amber-600 bg-amber-50 border-amber-100',
    },
    {
      title: 'Approved Revisions',
      value: summary.approved_revisions,
      icon: CheckCircle2,
      color: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    },
    {
      title: 'Rejected Revisions',
      value: summary.rejected_revisions,
      icon: XCircle,
      color: 'text-rose-600 bg-rose-50 border-rose-100',
    },
    {
      title: 'Requires Attention',
      value: summary.listings_requiring_attention,
      icon: AlertTriangle,
      color: 'text-orange-600 bg-orange-50 border-orange-100',
    },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Banner & Quick CTA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Compliance & Quality Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time overview of marketplace listings, policy validations, and AI quality reviews.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/listings/new"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold transition shadow-sm"
          >
            <PlusCircle className="w-4 h-4" />
            Create Listing
          </Link>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs hover:border-slate-300 transition-all flex flex-col justify-between"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  {card.title}
                </span>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center border ${card.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-4">
                <span className="text-3xl font-bold text-slate-900">{card.value}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Distribution & Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Distribution */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-indigo-600" />
            Policy Issues by Severity
          </h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                <span className="flex items-center gap-1.5 text-rose-700">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                  High Severity Violations
                </span>
                <span className="font-bold text-slate-900">{stats?.severity_distribution?.High || 0}</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div
                  className="bg-rose-500 h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, ((stats?.severity_distribution?.High || 0) / 10) * 100)}%`,
                  }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                <span className="flex items-center gap-1.5 text-amber-700">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  Medium Severity Warnings
                </span>
                <span className="font-bold text-slate-900">{stats?.severity_distribution?.Medium || 0}</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div
                  className="bg-amber-500 h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, ((stats?.severity_distribution?.Medium || 0) / 10) * 100)}%`,
                  }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                <span className="flex items-center gap-1.5 text-sky-700">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-500" />
                  Low Severity Quality Notes
                </span>
                <span className="font-bold text-slate-900">{stats?.severity_distribution?.Low || 0}</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div
                  className="bg-sky-500 h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, ((stats?.severity_distribution?.Low || 0) / 10) * 100)}%`,
                  }}
                />
              </div>
            </div>
          </div>
          <div className="mt-6 pt-4 border-t border-slate-100">
            <Link
              to="/policies"
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1.5"
            >
              <BookOpen className="w-3.5 h-3.5" />
              Manage Demonstration Policies &rarr;
            </Link>
          </div>
        </div>

        {/* Recent AI Reviews */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              Recent AI Reviews
            </h2>
            <Link to="/reviews" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800">
              View All &rarr;
            </Link>
          </div>

          {stats?.recent_reviews?.length === 0 ? (
            <EmptyState
              title="No AI reviews generated yet"
              description="Submit a listing for review to see automated policy evaluations."
            />
          ) : (
            <div className="divide-y divide-slate-100">
              {stats?.recent_reviews?.map((r) => (
                <div key={r.id} className="py-3 flex items-center justify-between gap-4">
                  <div>
                    <Link
                      to={`/reviews/${r.id}`}
                      className="text-sm font-semibold text-slate-900 hover:text-indigo-600 line-clamp-1"
                    >
                      {r.listing_title || `Listing #${r.listing_id}`}
                    </Link>
                    <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                      <span>Review #{r.id}</span>
                      <span>&bull;</span>
                      <span>{new Date(r.created_at).toLocaleDateString()}</span>
                      <span>&bull;</span>
                      <span className="font-mono text-[11px] bg-slate-100 px-1.5 py-0.2 rounded text-slate-600">
                        {r.model_name}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={r.overall_status} />
                    <Link
                      to={`/reviews/${r.id}`}
                      className="p-1.5 text-slate-400 hover:text-indigo-600 transition"
                    >
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Listings and Approval Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Listings */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Package className="w-4 h-4 text-indigo-600" />
              Recent Listings
            </h2>
            <Link to="/listings" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800">
              Manage Listings &rarr;
            </Link>
          </div>

          {stats?.recent_listings?.length === 0 ? (
            <EmptyState
              title="No listings yet"
              description="Create your first listing or import via CSV."
              actionText="Create Listing"
              onAction={() => window.location.assign('/listings/new')}
            />
          ) : (
            <div className="divide-y divide-slate-100">
              {stats?.recent_listings?.map((l) => (
                <div key={l.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <Link
                      to={`/listings/${l.id}`}
                      className="text-sm font-semibold text-slate-900 hover:text-indigo-600 truncate block"
                    >
                      {l.title}
                    </Link>
                    <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                      <span>{l.category}</span>
                      <span>&bull;</span>
                      <span className="font-semibold text-slate-700">
                        ${l.price.toFixed(2)} {l.currency}
                      </span>
                      <span>&bull;</span>
                      <span>Seller: {l.seller}</span>
                    </div>
                  </div>
                  <StatusBadge status={l.status} />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Human Approval Actions */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-indigo-600" />
              Recent Human Review Decisions
            </h2>
            <Link to="/history" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800">
              Full History &rarr;
            </Link>
          </div>

          {stats?.recent_actions?.length === 0 ? (
            <EmptyState
              title="No review actions taken"
              description="Human decisions on AI suggestions (Approve, Edit, Reject) will appear here."
            />
          ) : (
            <div className="divide-y divide-slate-100">
              {stats?.recent_actions?.map((a) => (
                <div key={a.id} className="py-3 flex items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs font-bold uppercase px-2 py-0.5 rounded ${
                          a.action === 'approve'
                            ? 'bg-emerald-100 text-emerald-800'
                            : a.action === 'edit'
                            ? 'bg-indigo-100 text-indigo-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {a.action}
                      </span>
                      <span className="text-xs font-medium text-slate-700">
                        by {a.actor_name || 'Reviewer'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1 line-clamp-1">
                      {a.comments || `Action on suggestion #${a.suggestion_id}`}
                    </p>
                  </div>
                  <span className="text-[11px] text-slate-400">
                    {new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
