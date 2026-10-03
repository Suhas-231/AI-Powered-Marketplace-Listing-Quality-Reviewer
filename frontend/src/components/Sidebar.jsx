import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ListOrdered,
  PlusCircle,
  Sparkles,
  BookOpen,
  History,
  Settings,
  ShieldCheck,
} from 'lucide-react';

export const Sidebar = () => {
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Listings', path: '/listings', icon: ListOrdered },
    { name: 'New Listing', path: '/listings/new', icon: PlusCircle },
    { name: 'AI Reviews', path: '/reviews', icon: Sparkles },
    { name: 'Policy Library', path: '/policies', icon: BookOpen },
    { name: 'Review History', path: '/history', icon: History },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col flex-shrink-0 min-h-screen">
      {/* Brand title area */}
      <div className="p-5 border-b border-slate-100 flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-md bg-indigo-600 flex items-center justify-center text-white">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-slate-900 leading-none">Reviewer Pro</h1>
          <span className="text-[10px] text-slate-400 font-medium">Compliance & Quality</span>
        </div>
      </div>

      {/* Nav links */}
      <nav className="p-3 space-y-1 flex-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700 font-semibold border border-indigo-100/80 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Knowledge Base Disclaimer Notice */}
      <div className="p-4 m-3 rounded-xl bg-slate-50 border border-slate-200/80 text-xs text-slate-600 space-y-1.5">
        <div className="flex items-center gap-1.5 font-semibold text-slate-800 text-[11px]">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
          Demonstration Mode
        </div>
        <p className="text-[11px] leading-relaxed text-slate-500">
          Sample demonstration policies active. Human reviewer approval required before applying revisions.
        </p>
      </div>
    </aside>
  );
};
