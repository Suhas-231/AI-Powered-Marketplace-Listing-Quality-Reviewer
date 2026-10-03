import React from 'react';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';

export const SeverityBadge = ({ severity }) => {
  const sev = (severity || 'Medium').toLowerCase();

  if (sev === 'high') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200">
        <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
        High Severity
      </span>
    );
  }

  if (sev === 'medium') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
        Medium Severity
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-sky-100 text-sky-800 border border-sky-200">
      <Info className="w-3.5 h-3.5 text-sky-600" />
      Low Severity
    </span>
  );
};
