import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  Sparkles,
  Edit,
  Trash2,
  Eye,
  Upload,
  Layers,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Loader2,
  CheckSquare,
  Square,
} from 'lucide-react';
import api from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { EmptyState } from '../components/EmptyState';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { CsvImportModal } from '../components/CsvImportModal';
import { BatchReviewModal } from '../components/BatchReviewModal';
import { useToast } from '../context/ToastContext';

export const Listings = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [listings, setListings] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [reviewingId, setReviewingId] = useState(null);

  // Filters & Pagination
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1', 10));
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [category, setCategory] = useState(searchParams.get('category') || 'all');
  const [status, setStatus] = useState(searchParams.get('status') || 'all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Modals & Batch Selection
  const [selectedIds, setSelectedIds] = useState([]);
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);

  const toast = useToast();

  const categories = [
    'Electronics & Gadgets',
    'Home & Kitchen',
    'Health & Personal Care',
    'Fashion & Apparel',
    'Beauty & Cosmetics',
    'Sports & Outdoors',
    'Books & Media',
    'Automotive & Tools',
    'Toys & Games',
    'Services & Consulting',
    'General Merchandise',
  ];

  const statuses = [
    { value: 'draft', label: 'Draft' },
    { value: 'pending_review', label: 'Pending Review' },
    { value: 'revisions_pending', label: 'Revisions Pending' },
    { value: 'revisions_applied', label: 'Revisions Applied' },
    { value: 'reviewed', label: 'Reviewed' },
    { value: 'approved', label: 'Approved' },
    { value: 'rejected', label: 'Rejected' },
  ];

  const fetchListings = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        per_page: 8,
        search,
        category: category !== 'all' ? category : undefined,
        status: status !== 'all' ? status : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      };
      const res = await api.get('/api/listings', { params });
      setListings(res.data.listings || []);
      setTotal(res.data.total || 0);
      setPages(res.data.pages || 1);
    } catch (err) {
      toast.error('Failed to load listings: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, [page, category, status, sortBy, sortOrder]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchListings();
  };

  const handleTriggerReview = async (listingId) => {
    try {
      setReviewingId(listingId);
      toast.info('Sending listing to Gemini for compliance review...');
      const res = await api.post(`/api/listings/${listingId}/review`);
      toast.success('AI Review generated successfully!');
      fetchListings();
      if (res.data?.review?.id) {
        window.location.assign(`/reviews/${res.data.review.id}`);
      }
    } catch (err) {
      toast.error(err.message || 'AI review failed');
    } finally {
      setReviewingId(null);
    }
  };

  const handleDeleteListing = async (listingId) => {
    if (!window.confirm(`Are you sure you want to delete listing #${listingId}?`)) return;
    try {
      await api.delete(`/api/listings/${listingId}`);
      toast.success(`Listing #${listingId} deleted.`);
      setSelectedIds((prev) => prev.filter((id) => id !== listingId));
      fetchListings();
    } catch (err) {
      toast.error('Failed to delete listing: ' + err.message);
    }
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === listings.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(listings.map((l) => l.id));
    }
  };

  const toggleSelectOne = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header and Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Marketplace Listings</h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse, manage, and trigger AI compliance reviews across products and services.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setIsCsvModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-2xs transition"
          >
            <Upload className="w-3.5 h-3.5 text-slate-500" />
            Import CSV
          </button>

          {selectedIds.length > 0 && (
            <button
              onClick={() => setIsBatchModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 hover:bg-indigo-100 text-xs font-semibold transition"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              Batch Review ({selectedIds.length})
            </button>
          )}

          <Link
            to="/listings/new"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-4 h-4" />
            Add Listing
          </Link>
        </div>
      </div>

      {/* Filters & Search Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search title, description, seller..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 text-slate-800 text-xs rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
          />
        </form>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Category Filter */}
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setPage(1);
            }}
            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Statuses</option>
            {statuses.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>

          {/* Sorting */}
          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [sb, so] = e.target.value.split('-');
              setSortBy(sb);
              setSortOrder(so);
            }}
            className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
          >
            <option value="created_at-desc">Newest First</option>
            <option value="created_at-asc">Oldest First</option>
            <option value="price-asc">Price: Low to High</option>
            <option value="price-desc">Price: High to Low</option>
          </select>
        </div>
      </div>

      {/* Listings Table / Cards */}
      {loading ? (
        <LoadingSkeleton count={4} />
      ) : listings.length === 0 ? (
        <EmptyState
          title="No listings found"
          description="Try adjusting your filters or search terms, or create a new listing."
          actionText="Create Listing"
          onAction={() => window.location.assign('/listings/new')}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-4 w-10 text-center">
                    <button
                      onClick={toggleSelectAll}
                      className="text-slate-500 hover:text-slate-800"
                      title="Select All"
                    >
                      {selectedIds.length === listings.length && listings.length > 0 ? (
                        <CheckSquare className="w-4 h-4 text-indigo-600" />
                      ) : (
                        <Square className="w-4 h-4" />
                      )}
                    </button>
                  </th>
                  <th className="py-3 px-4">Item Details</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Price</th>
                  <th className="py-3 px-4">Seller</th>
                  <th className="py-3 px-4">Review Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {listings.map((l) => {
                  const isSelected = selectedIds.includes(l.id);
                  const isReviewing = reviewingId === l.id;

                  return (
                    <tr
                      key={l.id}
                      className={`hover:bg-slate-50/60 transition-colors ${
                        isSelected ? 'bg-indigo-50/30' : ''
                      }`}
                    >
                      {/* Checkbox */}
                      <td className="py-3.5 px-4 text-center">
                        <button
                          onClick={() => toggleSelectOne(l.id)}
                          className="text-slate-400 hover:text-slate-700"
                        >
                          {isSelected ? (
                            <CheckSquare className="w-4 h-4 text-indigo-600" />
                          ) : (
                            <Square className="w-4 h-4" />
                          )}
                        </button>
                      </td>

                      {/* Title & Description snippet */}
                      <td className="py-3.5 px-4 max-w-sm">
                        <Link
                          to={`/listings/${l.id}`}
                          className="font-semibold text-slate-900 hover:text-indigo-600 line-clamp-1 block"
                        >
                          {l.title}
                        </Link>
                        <p className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">
                          {l.description}
                        </p>
                      </td>

                      {/* Category */}
                      <td className="py-3.5 px-4 text-slate-600 whitespace-nowrap">
                        {l.category}
                      </td>

                      {/* Price */}
                      <td className="py-3.5 px-4 font-semibold text-slate-900 whitespace-nowrap">
                        ${l.price.toFixed(2)} {l.currency}
                      </td>

                      {/* Seller */}
                      <td className="py-3.5 px-4 text-slate-600 whitespace-nowrap">
                        {l.seller}
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <StatusBadge status={l.status} />
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="inline-flex items-center gap-1.5">
                          {/* AI Review trigger button */}
                          <button
                            onClick={() => handleTriggerReview(l.id)}
                            disabled={isReviewing}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-[11px] font-semibold border border-indigo-200 transition disabled:opacity-50"
                            title="Run AI Policy Review"
                          >
                            {isReviewing ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Sparkles className="w-3 h-3 text-indigo-600" />
                            )}
                            Review
                          </button>

                          {/* View details */}
                          <Link
                            to={`/listings/${l.id}`}
                            className="p-1 text-slate-400 hover:text-slate-600 rounded transition"
                            title="View Listing"
                          >
                            <Eye className="w-4 h-4" />
                          </Link>

                          {/* Edit listing */}
                          <Link
                            to={`/listings/${l.id}/edit`}
                            className="p-1 text-slate-400 hover:text-slate-600 rounded transition"
                            title="Edit Listing"
                          >
                            <Edit className="w-4 h-4" />
                          </Link>

                          {/* Delete listing */}
                          <button
                            onClick={() => handleDeleteListing(l.id)}
                            className="p-1 text-slate-400 hover:text-rose-600 rounded transition"
                            title="Delete Listing"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination bar */}
          <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
            <div>
              Showing <span className="font-semibold text-slate-800">{listings.length}</span> of{' '}
              <span className="font-semibold text-slate-800">{total}</span> listings
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1 rounded border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-2">
                Page {page} of {pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(pages, p + 1))}
                disabled={page >= pages}
                className="p-1 rounded border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSV Import Modal */}
      <CsvImportModal
        isOpen={isCsvModalOpen}
        onClose={() => setIsCsvModalOpen(false)}
        onSuccess={() => {
          setIsCsvModalOpen(false);
          fetchListings();
        }}
      />

      {/* Batch Review Modal */}
      <BatchReviewModal
        isOpen={isBatchModalOpen}
        onClose={() => setIsBatchModalOpen(false)}
        selectedListingIds={selectedIds}
        onSuccess={() => {
          setSelectedIds([]);
          fetchListings();
        }}
      />
    </div>
  );
};
