import React from 'react';

export const LoadingSkeleton = ({ count = 3, type = 'card' }) => {
  return (
    <div className="space-y-4 animate-pulse">
      {Array.from({ length: count }).map((_, idx) => (
        <div
          key={idx}
          className="bg-white p-5 rounded-xl border border-slate-200 space-y-3"
        >
          <div className="flex items-center justify-between">
            <div className="h-4 bg-slate-200 rounded w-1/3" />
            <div className="h-4 bg-slate-200 rounded w-16" />
          </div>
          <div className="h-3 bg-slate-100 rounded w-full" />
          <div className="h-3 bg-slate-100 rounded w-4/5" />
          <div className="pt-2 flex gap-2">
            <div className="h-6 bg-slate-100 rounded w-20" />
            <div className="h-6 bg-slate-100 rounded w-24" />
          </div>
        </div>
      ))}
    </div>
  );
};
