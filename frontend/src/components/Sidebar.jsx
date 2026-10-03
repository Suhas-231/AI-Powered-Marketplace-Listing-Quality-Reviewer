import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  ListOrdered,
  PlusCircle,
  Sparkles,
  BookOpen,
  History,
  Settings,
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
      {/* Brand title area with uploaded Logo */}
      <div className="p-4 border-b border-slate-100">
        <Link to="/" className="flex items-center gap-3">
          <img
            src="/logo.png"
            alt="Reviewer Pro"
            className="h-10 w-auto object-contain flex-shrink-0"
          />
          <div className="min-w-0">
            <h1 className="text-sm font-bold text-slate-900 leading-tight truncate">Reviewer Pro</h1>
            <span className="text-[10px] text-slate-400 font-medium block truncate">Marketplace Quality</span>
          </div>
        </Link>
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
    </aside>
  );
};
