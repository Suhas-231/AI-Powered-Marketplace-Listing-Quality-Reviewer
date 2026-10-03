import React from 'react';
import { Search, User } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';

export const Navbar = ({ searchQuery, setSearchQuery }) => {
  const navigate = useNavigate();

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery) {
      navigate(`/listings?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 sticky top-0 z-30 flex items-center justify-between px-6">
      {/* Brand Logo & Application Title */}
      <div className="flex items-center gap-3">
        <Link to="/" className="flex items-center gap-3 font-bold text-slate-900 text-lg tracking-tight hover:opacity-95 transition">
          <img
            src="/logo.png"
            alt="Reviewer Pro Logo"
            className="h-10 w-auto object-contain"
          />
          <span className="hidden sm:inline">Marketplace Listing Quality Reviewer</span>
        </Link>
      </div>

      {/* Center Search Input */}
      <div className="hidden sm:flex items-center max-w-md w-full mx-6">
        <form onSubmit={handleSearchSubmit} className="relative w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search listings, sellers, keywords..."
            value={searchQuery || ''}
            onChange={(e) => setSearchQuery && setSearchQuery(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 text-slate-800 text-sm rounded-lg pl-9 pr-4 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
          />
        </form>
      </div>

      {/* Right User & Status Area */}
      <div className="flex items-center gap-4">
        <div className="hidden lg:flex flex-col text-right">
          <span className="text-xs font-semibold text-slate-900">Suhas</span>
          <span className="text-[11px] text-slate-500 font-medium">Senior Reviewer & Compliance Officer</span>
        </div>
        <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600">
          <User className="w-4 h-4" />
        </div>
      </div>
    </header>
  );
};
