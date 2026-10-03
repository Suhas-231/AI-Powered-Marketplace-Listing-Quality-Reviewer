import React, { useState, useEffect } from 'react';
import { X, Sparkles, CheckCircle2, AlertCircle, Loader2, ArrowRight, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useToast } from '../context/ToastContext';

export const BatchReviewModal = ({ isOpen, onClose, selectedListingIds = [], onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [completed, setCompleted] = useState(false);
  const toast = useToast();

  useEffect(() => {
    if (isOpen) {
      setResults([]);
      setCompleted(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleStartBatchReview = async () => {
    if (!selectedListingIds.length) {
      toast.warning('No listings selected for review.');
      return;
    }

    setLoading(true);
    setResults([]);

    try {
      const response = await api.post('/api/batch/review', {
        listing_ids: selectedListingIds,
      });

      setResults(response.data.results || []);
      setCompleted(true);
      toast.success(
        `Batch review finished: ${response.data.successful} passed, ${response.data.failed} failed.`
      );
      if (onSuccess) onSuccess();
    } catch (err) {
      toast.error(err.message || 'Batch review execution failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRetryFailed = async () => {
    const failedIds = results.filter((r) => r.status === 'failed').map((r) => r.listing_id);
    if (!failedIds.length) return;

    setLoading(true);
    try {
      const response = await api.post('/api/batch/review', {
        listing_ids: failedIds,
      });

      // Update result state with retried items
      const updated = results.map((r) => {
        const retried = response.data.results.find((res) => res.listing_id === r.listing_id);
        return retried || r;
      });
      setResults(updated);
      toast.success('Retry attempt completed.');
      if (onSuccess) onSuccess();
    } catch (err) {
      toast.error(err.message || 'Retry failed');
    } finally {
      setLoading(false);
    }
  };

  const hasFailed = results.some((r) => r.status === 'failed');

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">Batch AI Policy Review</h3>
              <p className="text-xs text-slate-500">
                Evaluating {selectedListingIds.length} listing{selectedListingIds.length === 1 ? '' : 's'} sequentially
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4">
          {!completed && !loading && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 leading-relaxed">
              <p className="font-semibold text-slate-800 mb-1">Workflow Overview:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Each listing undergoes deterministic schema and business rule validation.</li>
                <li>Relevant marketplace policies are retrieved from the knowledge base.</li>
                <li>Google Gemini evaluates content against compliance guidelines.</li>
                <li>Individual review results and human-review suggestions are saved to the database.</li>
              </ul>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center py-10 space-y-3">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
              <p className="text-sm font-semibold text-slate-800">Processing Batch Review...</p>
              <p className="text-xs text-slate-500">
                Calling Gemini API sequentially with safe rate limit pacing. Please wait.
              </p>
            </div>
          )}

          {completed && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-semibold pb-1 border-b border-slate-100">
                <span>Processed Results:</span>
                <div className="flex gap-3">
                  <span className="text-emerald-600">
                    {results.filter((r) => r.status === 'success').length} Passed
                  </span>
                  <span className="text-rose-600">
                    {results.filter((r) => r.status === 'failed').length} Failed
                  </span>
                </div>
              </div>

              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {results.map((r, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-xl border text-xs flex items-center justify-between ${
                      r.status === 'success'
                        ? 'bg-emerald-50/60 border-emerald-200 text-emerald-900'
                        : 'bg-rose-50/60 border-rose-200 text-rose-900'
                    }`}
                  >
                    <div className="flex items-start gap-2.5">
                      {r.status === 'success' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 flex-shrink-0" />
                      )}
                      <div>
                        <div className="font-semibold line-clamp-1">
                          Listing #{r.listing_id} {r.listing_title ? `— ${r.listing_title}` : ''}
                        </div>
                        <div className="text-[11px] opacity-80 mt-0.5">
                          {r.status === 'success'
                            ? `Status: ${r.overall_status} • Found ${r.findings_count} policy item(s)`
                            : `Reason: ${r.error}`}
                        </div>
                      </div>
                    </div>

                    {r.review_id && (
                      <Link
                        to={`/reviews/${r.review_id}`}
                        onClick={onClose}
                        className="inline-flex items-center gap-1 font-semibold text-indigo-600 hover:text-indigo-800 bg-white border border-indigo-100 px-2.5 py-1 rounded-md text-[11px] shadow-2xs"
                      >
                        Open Report
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            {hasFailed && !loading && (
              <button
                type="button"
                onClick={handleRetryFailed}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-rose-700 hover:text-rose-900"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retry Failed Listings
              </button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800"
            >
              {completed ? 'Close' : 'Cancel'}
            </button>
            {!completed && (
              <button
                type="button"
                onClick={handleStartBatchReview}
                disabled={loading || selectedListingIds.length === 0}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white transition shadow-sm disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                Execute Review ({selectedListingIds.length})
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
