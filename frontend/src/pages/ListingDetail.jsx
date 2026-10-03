import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Sparkles,
  Edit,
  Tag,
  Store,
  DollarSign,
  Layers,
  Clock,
  ArrowRight,
  ShieldAlert,
  Loader2,
} from 'lucide-react';
import api from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { useToast } from '../context/ToastContext';

export const ListingDetail = () => {
  const { id } = useParams();
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();

  const fetchListing = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/api/listings/${id}`);
      setListing(res.data);
    } catch (err) {
      toast.error('Failed to load listing: ' + err.message);
      navigate('/listings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListing();
  }, [id]);

  const handleTriggerReview = async () => {
    try {
      setReviewing(true);
      toast.info('Sending listing to Gemini for compliance evaluation...');
      const res = await api.post(`/api/listings/${id}/review`);
      toast.success('AI Review generated successfully!');
      if (res.data?.review?.id) {
        navigate(`/reviews/${res.data.review.id}`);
      } else {
        fetchListing();
      }
    } catch (err) {
      toast.error(err.message || 'AI review failed');
    } finally {
      setReviewing(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 space-y-6 max-w-5xl mx-auto">
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  if (!listing) return null;

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <Link
            to="/listings"
            className="p-2 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-slate-800 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">{listing.title}</h1>
              <StatusBadge status={listing.status} />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Listing ID #{listing.id} &bull; Created {new Date(listing.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            to={`/listings/${listing.id}/edit`}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-2xs transition"
          >
            <Edit className="w-3.5 h-3.5" />
            Edit Listing
          </Link>

          <button
            onClick={handleTriggerReview}
            disabled={reviewing}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition disabled:opacity-50"
          >
            {reviewing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Reviewing...
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                Run AI Review
              </>
            )}
          </button>
        </div>
      </div>

      {/* Grid: Details & Review History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Listing Data */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-4">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Description & Specifications
            </h2>
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line bg-slate-50 p-4 rounded-xl border border-slate-100">
              {listing.description}
            </p>

            {/* Attributes */}
            {listing.attributes && Object.keys(listing.attributes).length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Technical Specifications
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(listing.attributes).map(([k, v]) => (
                    <div key={k} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs">
                      <span className="font-semibold text-slate-600">{k}:</span>{' '}
                      <span className="text-slate-900">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tags */}
            {listing.tags && listing.tags.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Search Tags
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {listing.tags.map((t, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md"
                    >
                      <Tag className="w-3 h-3 text-slate-400" />
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Metadata & Reviews Timeline */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-3 text-xs">
            <h2 className="font-bold text-slate-800 uppercase tracking-wider mb-2">Item Metadata</h2>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Category:</span>
              <span className="font-semibold text-slate-800">{listing.category}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Price:</span>
              <span className="font-semibold text-slate-900">
                ${listing.price.toFixed(2)} {listing.currency}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Seller / Vendor:</span>
              <span className="font-semibold text-slate-800">{listing.seller}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Type:</span>
              <span className="font-semibold text-slate-800">{listing.listing_type}</span>
            </div>
          </div>

          {/* AI Reviews for this listing */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-3">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              AI Compliance Reviews ({listing.reviews?.length || 0})
            </h2>

            {!listing.reviews || listing.reviews.length === 0 ? (
              <p className="text-xs text-slate-500 py-3">
                No reviews yet. Click 'Run AI Review' to inspect policy compliance.
              </p>
            ) : (
              <div className="space-y-2.5">
                {listing.reviews.map((rev) => (
                  <Link
                    key={rev.id}
                    to={`/reviews/${rev.id}`}
                    className="p-3 rounded-xl border border-slate-200 hover:border-indigo-300 bg-slate-50/50 hover:bg-indigo-50/20 transition block space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900">Review #{rev.id}</span>
                      <StatusBadge status={rev.overall_status} />
                    </div>
                    <p className="text-[11px] text-slate-500 line-clamp-1">{rev.summary}</p>
                    <div className="flex items-center justify-between pt-1 text-[11px] text-indigo-600 font-semibold">
                      <span>{rev.findings?.length || 0} findings recorded</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
