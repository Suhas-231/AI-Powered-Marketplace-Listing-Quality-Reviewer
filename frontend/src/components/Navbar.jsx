import React, { useState, useRef, useEffect } from 'react';
import { Search, User, ChevronDown, Edit3, Shield, Mail } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { ProfileModal } from './ProfileModal';

export const Navbar = ({ searchQuery, setSearchQuery }) => {
  const navigate = useNavigate();
  const { user, loading } = useUser();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('view');
  const dropdownRef = useRef(null);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery) {
      navigate(`/listings?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownOpen]);

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && dropdownOpen) {
        setDropdownOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [dropdownOpen]);

  const userName = user?.name || (loading ? 'Loading...' : 'Reviewer');
  const userRole = user?.role || 'Compliance Reviewer';
  const userInitial = (user?.name || 'U').charAt(0).toUpperCase();

  const handleOpenViewProfile = () => {
    setDropdownOpen(false);
    setModalMode('view');
    setProfileModalOpen(true);
  };

  const handleOpenEditProfile = () => {
    setDropdownOpen(false);
    setModalMode('edit');
    setProfileModalOpen(true);
  };

  return (
    <>
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

        {/* Right User & Profile Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setDropdownOpen((prev) => !prev)}
            aria-expanded={dropdownOpen}
            aria-label="User profile menu"
            className="flex items-center gap-3 p-1.5 rounded-xl hover:bg-slate-50 transition border border-transparent hover:border-slate-200 focus:outline-none"
          >
            <div className="hidden lg:flex flex-col text-right">
              <span className="text-xs font-semibold text-slate-900 leading-tight">
                {userName}
              </span>
              <span className="text-[11px] text-slate-500 font-medium">
                {userRole}
              </span>
            </div>

            <div className="w-9 h-9 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-sm shadow-xs border border-indigo-700/20 flex-shrink-0">
              {userInitial}
            </div>

            <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-150 ${dropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Profile Dropdown Menu */}
          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl border border-slate-200 shadow-xl py-2 z-40 animate-in fade-in zoom-in-95 duration-100">
              {/* User Identity Header */}
              <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-sm flex-shrink-0">
                    {userInitial}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-slate-900 truncate">
                      {userName}
                    </p>
                    <p className="text-[11px] text-slate-500 truncate flex items-center gap-1 mt-0.5">
                      <Mail className="w-3 h-3 text-slate-400 flex-shrink-0" />
                      {user?.email || 'compliance@marketplace.local'}
                    </p>
                  </div>
                </div>
                <div className="mt-2.5 flex items-center gap-1">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100">
                    <Shield className="w-2.5 h-2.5" />
                    {userRole}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono ml-auto">
                    ID #{user?.id || 1}
                  </span>
                </div>
              </div>

              {/* Menu Actions */}
              <div className="p-1 space-y-0.5">
                <button
                  type="button"
                  onClick={handleOpenViewProfile}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-700 hover:text-indigo-600 hover:bg-indigo-50/60 rounded-xl transition text-left"
                >
                  <User className="w-4 h-4 text-slate-400 group-hover:text-indigo-600" />
                  View Profile
                </button>

                <button
                  type="button"
                  onClick={handleOpenEditProfile}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-700 hover:text-indigo-600 hover:bg-indigo-50/60 rounded-xl transition text-left"
                >
                  <Edit3 className="w-4 h-4 text-slate-400 group-hover:text-indigo-600" />
                  Edit Profile
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Profile Modal */}
      <ProfileModal
        isOpen={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
        initialMode={modalMode}
      />
    </>
  );
};
