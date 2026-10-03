import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Sparkles,
  CheckCircle2,
  XCircle,
  Edit3,
  AlertTriangle,
  AlertCircle,
  Info,
  BookOpen,
  Check,
  X,
  RotateCcw,
  ShieldAlert,
  Loader2,
  Trash2,
} from 'lucide-react';
import api from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { SeverityBadge } from '../components/SeverityBadge';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { useToast } from '../context/ToastContext';

export const ReviewReport = () => {
  const { id } = useParams();
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingSuggestionId, setEditingSuggestionId] = useState(null);
  const [editText, setEditText] = useState('');
  const [rejectingSuggestionId, setRejectingSuggestionId] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();

  const fetchReview = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/api/reviews/${id}`);
      setReview(res.data);
    } catch (err) {
      toast.error('Failed to load review: ' + err.message);
      navigate('/reviews');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReview();
  }, [id]);

  const handleApprove = async (suggestionId, customFinalValue = null) => {
    try {
      setActionLoading(true);
      const payload = customFinalValue ? { final_value: customFinalValue } : {};
      await api.post(`/api/suggestions/${suggestionId}/approve`, payload);
      toast.success('Revision approved and applied to listing field!');
      fetchReview();
    } catch (err) {
      toast.error(err.message || 'Failed to approve revision');
    } finally {
      setActionLoading(false);
      setEditingSuggestionId(null);
    }
  };

  const handleStartEdit = (suggestion) => {
    setEditingSuggestionId(suggestion.id);
    setEditText(suggestion.final_value || suggestion.suggested_value);
  };

  const handleSaveEditAndApprove = async (suggestionId) => {
    if (!editText.trim()) {
      toast.error('Replacement text cannot be empty');
      return;
    }
    handleApprove(suggestionId, editText.trim());
  };

  const handleReject = async (suggestionId) => {
    try {
      setActionLoading(true);
      await api.post(`/api/suggestions/${suggestionId}/reject`, {
        reason: rejectionReason || 'Rejected by human reviewer',
      });
      toast.info('Suggestion rejected. Original listing content retained intact.');
      setRejectingSuggestionId(null);
      setRejectionReason('');
      fetchReview();
    } catch (err) {
      toast.error(err.message || 'Failed to reject suggestion');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteReview = async () => {
    if (!window.confirm(`Are you sure you want to permanently delete review #${review.id}? This will remove all findings and suggestions permanently.`)) {
      return;
    }
    try {
      setActionLoading(true);
      await api.delete(`/api/reviews/${review.id}`);
      toast.success(`Review #${review.id} has been permanently deleted.`);
      navigate('/reviews');
    } catch (err) {
      toast.error(err.message || 'Failed to delete review');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 space-y-6 max-w-6xl mx-auto">
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  if (!review) return null;

  const totalFindings = review.findings?.length || 0;
  const approvedCount = review.findings?.filter(
    (f) => f.suggestion?.action_status === 'approved'
  ).length || 0;
  const rejectedCount = review.findings?.filter(
    (f) => f.suggestion?.action_status === 'rejected'
  ).length || 0;
  const pendingCount = review.findings?.filter(
    (f) => !f.suggestion || f.suggestion.action_status === 'pending'
  ).length || 0;

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      {/* Top Navigation & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <Link
            to="/reviews"
            className="p-2 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-slate-800 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Review Report #{review.id}
              </h1>
              <StatusBadge status={review.overall_status} />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Target Listing:{' '}
              <Link
                to={`/listings/${review.listing_id}`}
                className="font-semibold text-indigo-600 hover:underline"
              >
                {review.listing_title || `Listing #${review.listing_id}`}
              </Link>{' '}
              &bull; {new Date(review.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleDeleteReview}
          disabled={actionLoading}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white border border-rose-200 text-rose-700 hover:bg-rose-50 text-xs font-semibold shadow-2xs transition"
          title="Permanently delete this review"
        >
          <Trash2 className="w-3.5 h-3.5 text-rose-600" />
          Delete Review
        </button>
      </div>

      {/* Mandatory Demonstration Notice Banner */}
      <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3 text-xs text-amber-900">
        <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Demonstration policy knowledge base:</span> Replace these sample
          rules with the official marketplace policy before production use. No AI suggestion is applied to
          listings without explicit human approval below.
        </div>
      </div>

      {/* Summary KPI Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
            Total Issues
          </span>
          <span className="text-2xl font-bold text-slate-900 mt-1 block">{totalFindings}</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-rose-200/80 bg-rose-50/20 shadow-2xs">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-rose-700 block">
            High Severity
          </span>
          <span className="text-2xl font-bold text-rose-600 mt-1 block">
            {review.severity_counts?.high || 0}
          </span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-amber-200/80 bg-amber-50/20 shadow-2xs">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-700 block">
            Medium Severity
          </span>
          <span className="text-2xl font-bold text-amber-600 mt-1 block">
            {review.severity_counts?.medium || 0}
          </span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-sky-200/80 bg-sky-50/20 shadow-2xs">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-700 block">
            Low Severity
          </span>
          <span className="text-2xl font-bold text-sky-600 mt-1 block">
            {review.severity_counts?.low || 0}
          </span>
        </div>
      </div>

      {/* AI Summary Card & Assumptions */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-4">
        <div>
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-1">
            Executive Quality Summary
          </h2>
          <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
            {review.summary}
          </p>
        </div>

        {/* Assumptions / Unverifiable claims */}
        {(review.assumptions?.length > 0 || review.unverifiable_claims?.length > 0) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-100">
            {review.assumptions?.length > 0 && (
              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/60 text-xs">
                <span className="font-bold text-slate-800 block mb-1">AI Evaluator Assumptions:</span>
                <ul className="list-disc list-inside space-y-0.5 text-slate-600">
                  {review.assumptions.map((a, i) => (
                    <li key={i}>{a}</li>
                  ))}
                </ul>
              </div>
            )}
            {review.unverifiable_claims?.length > 0 && (
              <div className="bg-amber-50/60 p-3.5 rounded-xl border border-amber-200 text-xs">
                <span className="font-bold text-amber-900 block mb-1">Unverifiable Claims Detected:</span>
                <ul className="list-disc list-inside space-y-0.5 text-amber-800">
                  {review.unverifiable_claims.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Progress Bar for Human Review Decisions */}
        <div className="pt-2 border-t border-slate-100">
          <div className="flex items-center justify-between text-xs text-slate-600 mb-1.5 font-medium">
            <span>Human Review Decision Progress:</span>
            <span>
              {approvedCount + rejectedCount} of {totalFindings} findings reviewed ({pendingCount} pending)
            </span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden flex">
            <div
              className="bg-emerald-500 h-full transition-all"
              style={{ width: `${totalFindings ? (approvedCount / totalFindings) * 100 : 0}%` }}
              title={`Approved: ${approvedCount}`}
            />
            <div
              className="bg-rose-500 h-full transition-all"
              style={{ width: `${totalFindings ? (rejectedCount / totalFindings) * 100 : 0}%` }}
              title={`Rejected: ${rejectedCount}`}
            />
          </div>
        </div>
      </div>

      {/* Findings Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            Detailed Policy Findings & Suggested Revisions ({totalFindings})
          </h2>
          <span className="text-xs text-slate-500">
            Action each finding individually (Approve, Edit, Reject).
          </span>
        </div>

        {totalFindings === 0 ? (
          <div className="bg-white p-8 rounded-xl border border-slate-200 text-center text-sm text-slate-500">
            No compliance issues identified in this listing.
          </div>
        ) : (
          <div className="space-y-4">
            {review.findings.map((f, idx) => {
              const suggestion = f.suggestion;
              const actionStatus = suggestion?.action_status || 'pending';
              const isEditing = editingSuggestionId === suggestion?.id;
              const isRejecting = rejectingSuggestionId === suggestion?.id;

              return (
                <div
                  key={f.id}
                  className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden transition hover:border-slate-300"
                >
                  {/* Finding Header */}
                  <div className="px-6 py-4 bg-slate-50/75 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <span className="w-6 h-6 rounded-full bg-slate-200 text-slate-700 text-xs font-bold flex items-center justify-center">
                        {idx + 1}
                      </span>
                      <span className="font-bold text-xs uppercase tracking-wider text-slate-700">
                        Field: <span className="text-indigo-600 capitalize">{f.field_name}</span>
                      </span>
                      <span className="text-slate-300">&bull;</span>
                      <span className="text-xs text-slate-500 font-medium capitalize">
                        Type: {f.issue_type.replace('_', ' ')}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <SeverityBadge severity={f.severity} />

                      {/* Status indicator for this suggestion */}
                      {actionStatus === 'approved' && (
                        <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-md">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Approved & Applied
                        </span>
                      )}
                      {actionStatus === 'rejected' && (
                        <span className="inline-flex items-center gap-1 text-xs font-bold text-rose-700 bg-rose-100 px-2.5 py-1 rounded-md">
                          <XCircle className="w-3.5 h-3.5" /> Rejected
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Finding Body */}
                  <div className="p-6 space-y-4">
                    {/* Explanation & Policy Citation */}
                    <div className="text-xs space-y-1.5">
                      <p className="text-slate-800 font-medium text-sm leading-relaxed">
                        {f.issue_description}
                      </p>
                      {f.explanation && (
                        <p className="text-slate-500 leading-normal">{f.explanation}</p>
                      )}

                      <div className="flex items-center gap-2 pt-1 text-indigo-700 font-semibold">
                        <BookOpen className="w-3.5 h-3.5" />
                        <span>Cited Policy: {f.policy_reference_code || 'DEMO-POLICY'}</span>
                        {f.policy_title && (
                          <span className="text-slate-500 font-normal">&mdash; {f.policy_title}</span>
                        )}
                      </div>
                    </div>

                    {/* Diff Comparison: Original vs Suggested / Final */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      {/* Original Content */}
                      <div className="p-4 rounded-xl bg-rose-50/50 border border-rose-200/80 space-y-1.5">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-rose-700 flex items-center gap-1">
                          <X className="w-3.5 h-3.5" /> Original Listing Content
                        </span>
                        <p className="text-slate-800 font-mono text-[11px] leading-relaxed break-words whitespace-pre-wrap">
                          {f.original_value}
                        </p>
                      </div>

                      {/* AI Suggested or Final Edited Content */}
                      <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-200/80 space-y-1.5">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1">
                          <Check className="w-3.5 h-3.5" />
                          {actionStatus === 'approved' ? 'Approved Replacement Content' : 'AI Suggested Revision'}
                        </span>

                        {isEditing ? (
                          <div className="space-y-2 pt-1">
                            <textarea
                              rows={3}
                              value={editText}
                              onChange={(e) => setEditText(e.target.value)}
                              className="w-full text-xs font-mono bg-white border border-emerald-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            />
                            <div className="flex items-center gap-2 justify-end">
                              <button
                                type="button"
                                onClick={() => setEditingSuggestionId(null)}
                                className="px-2.5 py-1 text-slate-500 hover:text-slate-700 font-medium"
                              >
                                Cancel
                              </button>
                              <button
                                type="button"
                                onClick={() => handleSaveEditAndApprove(suggestion.id)}
                                disabled={actionLoading}
                                className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-semibold flex items-center gap-1 shadow-xs"
                              >
                                {actionLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                                Apply Edited
                              </button>
                            </div>
                          </div>
                        ) : (
                          <p className="text-slate-800 font-mono text-[11px] leading-relaxed break-words whitespace-pre-wrap">
                            {suggestion?.final_value || f.suggested_revision}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Rejection input dialog if rejecting */}
                    {isRejecting && (
                      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                        <span className="font-semibold text-slate-800">
                          Provide optional reason for rejecting this suggestion:
                        </span>
                        <input
                          type="text"
                          value={rejectionReason}
                          onChange={(e) => setRejectionReason(e.target.value)}
                          placeholder="e.g. Seller provided valid external certification / intentional wording"
                          className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500"
                        />
                        <div className="flex items-center justify-end gap-2 pt-1">
                          <button
                            type="button"
                            onClick={() => setRejectingSuggestionId(null)}
                            className="px-3 py-1 text-slate-500 hover:text-slate-700"
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            onClick={() => handleReject(suggestion.id)}
                            disabled={actionLoading}
                            className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded font-semibold"
                          >
                            Confirm Rejection
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Human Action Buttons Bar */}
                    {suggestion && (
                      <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                        <div className="text-[11px] text-slate-500">
                          {suggestion.reviewed_by && (
                            <span>
                              Reviewed by {suggestion.reviewer_name || 'Reviewer'} at{' '}
                              {new Date(suggestion.reviewed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          )}
                          {suggestion.rejection_reason && (
                            <span className="text-rose-600 block">
                              Reason: {suggestion.rejection_reason}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          {/* Approve Button */}
                          <button
                            type="button"
                            onClick={() => handleApprove(suggestion.id)}
                            disabled={actionLoading || actionStatus === 'approved' || actionStatus === 'rejected'}
                            title={
                              actionStatus === 'approved'
                                ? 'Approved and applied to listing'
                                : actionStatus === 'rejected'
                                ? 'Blocked: Suggestion has been rejected'
                                : 'Approve this revision'
                            }
                            className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                              actionStatus === 'approved'
                                ? 'bg-emerald-100 text-emerald-800 cursor-default opacity-90'
                                : actionStatus === 'rejected'
                                ? 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed opacity-40'
                                : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs'
                            }`}
                          >
                            <Check className="w-3.5 h-3.5" />
                            {actionStatus === 'approved' ? 'Approved' : 'Approve Revision'}
                          </button>

                          {/* Edit Button */}
                          {!isEditing && (
                            <button
                              type="button"
                              onClick={() => handleStartEdit(suggestion)}
                              disabled={actionLoading || actionStatus === 'approved' || actionStatus === 'rejected'}
                              title={
                                actionStatus === 'approved'
                                  ? 'Blocked: Revision already approved and applied'
                                  : actionStatus === 'rejected'
                                  ? 'Blocked: Suggestion has been rejected'
                                  : 'Edit revision wording'
                              }
                              className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                                actionStatus === 'approved' || actionStatus === 'rejected'
                                  ? 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed opacity-40'
                                  : 'bg-white border border-slate-200 hover:bg-slate-50 text-slate-700'
                              }`}
                            >
                              <Edit3 className="w-3.5 h-3.5 text-slate-500" />
                              Edit Revision
                            </button>
                          )}

                          {/* Reject Button */}
                          {!isRejecting && (
                            <button
                              type="button"
                              onClick={() => setRejectingSuggestionId(suggestion.id)}
                              disabled={actionLoading || actionStatus === 'rejected' || actionStatus === 'approved'}
                              title={
                                actionStatus === 'rejected'
                                  ? 'Rejected (Original content retained)'
                                  : actionStatus === 'approved'
                                  ? 'Blocked: Revision has already been approved'
                                  : 'Reject this suggestion'
                              }
                              className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                                actionStatus === 'rejected'
                                  ? 'bg-rose-100 text-rose-800 cursor-default opacity-90'
                                  : actionStatus === 'approved'
                                  ? 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed opacity-40'
                                  : 'bg-white border border-rose-200 text-rose-700 hover:bg-rose-50'
                              }`}
                            >
                              <X className="w-3.5 h-3.5" />
                              {actionStatus === 'rejected' ? 'Rejected' : 'Reject'}
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
