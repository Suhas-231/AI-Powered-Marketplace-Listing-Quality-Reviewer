import React from 'react';

export const StatusBadge = ({ status }) => {
  const normalized = (status || 'draft').toLowerCase().replace(' ', '_');

  const config = {
    draft: { bg: 'bg-slate-100 text-slate-700 border-slate-200', label: 'Draft' },
    pending_review: { bg: 'bg-amber-50 text-amber-700 border-amber-200', label: 'Pending Review' },
    revisions_pending: { bg: 'bg-orange-50 text-orange-700 border-orange-200', label: 'Revisions Pending' },
    revisions_applied: { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', label: 'Revisions Applied' },
    approved: { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', label: 'Approved' },
    rejected: { bg: 'bg-rose-50 text-rose-700 border-rose-200', label: 'Rejected' },
    flagged: { bg: 'bg-rose-50 text-rose-700 border-rose-200', label: 'Flagged' },
    needs_review: { bg: 'bg-indigo-50 text-indigo-700 border-indigo-200', label: 'Needs Review' },
    compliant: { bg: 'bg-teal-50 text-teal-700 border-teal-200', label: 'Compliant' },
    completed: { bg: 'bg-blue-50 text-blue-700 border-blue-200', label: 'Completed' },
    failed: { bg: 'bg-rose-50 text-rose-700 border-rose-200', label: 'Failed' },
  };

  const current = config[normalized] || {
    bg: 'bg-slate-100 text-slate-700 border-slate-200',
    label: status || 'Unknown',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${current.bg}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70 mr-1.5" />
      {current.label}
    </span>
  );
};
