import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './context/ToastContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';

import { Dashboard } from './pages/Dashboard';
import { Listings } from './pages/Listings';
import { ListingForm } from './pages/ListingForm';
import { ListingDetail } from './pages/ListingDetail';
import { AIReviews } from './pages/AIReviews';
import { ReviewReport } from './pages/ReviewReport';
import { PolicyLibrary } from './pages/PolicyLibrary';
import { ReviewHistory } from './pages/ReviewHistory';
import { Settings } from './pages/Settings';

export default function App() {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <ToastProvider>
      <BrowserRouter>
        <div className="flex min-h-screen bg-slate-50 font-sans text-slate-800">
          {/* Left Navigation Sidebar */}
          <Sidebar />

          {/* Main App Content Area */}
          <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
            {/* Top Navigation Bar */}
            <Navbar searchQuery={searchQuery} setSearchQuery={setSearchQuery} />

            {/* Page Router View */}
            <main className="flex-1 overflow-y-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/listings" element={<Listings />} />
                <Route path="/listings/new" element={<ListingForm />} />
                <Route path="/listings/:id" element={<ListingDetail />} />
                <Route path="/listings/:id/edit" element={<ListingForm />} />
                <Route path="/reviews" element={<AIReviews />} />
                <Route path="/reviews/:id" element={<ReviewReport />} />
                <Route path="/policies" element={<PolicyLibrary />} />
                <Route path="/history" element={<ReviewHistory />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </ToastProvider>
  );
}
