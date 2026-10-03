import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Save,
  Sparkles,
  Plus,
  Trash2,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Loader2,
} from 'lucide-react';
import api from '../api/client';
import { useToast } from '../context/ToastContext';

export const ListingForm = () => {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const toast = useToast();

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    price: '',
    currency: 'INR',
    listing_type: 'Product',
    seller: '',
    tags: '',
    attributes: [{ key: '', value: '' }],
  });

  const [loading, setLoading] = useState(false);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const [validationWarnings, setValidationWarnings] = useState([]);

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

  const currencies = ['INR', 'USD', 'EUR', 'GBP', 'CAD', 'AUD'];

  useEffect(() => {
    if (isEdit) {
      const fetchListing = async () => {
        try {
          setLoading(true);
          const res = await api.get(`/api/listings/${id}`);
          const item = res.data;

          // Convert attributes dict to array of {key, value}
          const attrsArray = item.attributes
            ? Object.entries(item.attributes).map(([k, v]) => ({ key: k, value: String(v) }))
            : [{ key: '', value: '' }];

          setFormData({
            title: item.title || '',
            description: item.description || '',
            category: item.category || '',
            price: item.price !== undefined ? String(item.price) : '',
            currency: item.currency || 'INR',
            listing_type: item.listing_type || 'Product',
            seller: item.seller || '',
            tags: Array.isArray(item.tags) ? item.tags.join(', ') : '',
            attributes: attrsArray.length > 0 ? attrsArray : [{ key: '', value: '' }],
          });
        } catch (err) {
          toast.error('Failed to load listing for editing: ' + err.message);
          navigate('/listings');
        } finally {
          setLoading(false);
        }
      };
      fetchListing();
    }
  }, [id, isEdit, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error for that field if present
    if (validationErrors[name]) {
      setValidationErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  const handleAttributeChange = (index, field, val) => {
    setFormData((prev) => {
      const updated = [...prev.attributes];
      updated[index][field] = val;
      return { ...prev, attributes: updated };
    });
  };

  const addAttributeRow = () => {
    setFormData((prev) => ({
      ...prev,
      attributes: [...prev.attributes, { key: '', value: '' }],
    }));
  };

  const removeAttributeRow = (index) => {
    setFormData((prev) => ({
      ...prev,
      attributes: prev.attributes.filter((_, i) => i !== index),
    }));
  };

  const buildPayload = () => {
    // Convert attributes array back to dict
    const attrDict = {};
    formData.attributes.forEach(({ key, value }) => {
      if (key.trim()) {
        attrDict[key.trim()] = value.trim();
      }
    });

    const tagsArray = formData.tags
      ? formData.tags.split(',').map((t) => t.trim()).filter(Boolean)
      : [];

    return {
      title: formData.title,
      description: formData.description,
      category: formData.category,
      price: formData.price,
      currency: formData.currency,
      listing_type: formData.listing_type,
      seller: formData.seller,
      tags: tagsArray,
      attributes: attrDict,
    };
  };

  const handleSubmit = async (e, submitForReview = false) => {
    e.preventDefault();
    setValidationErrors({});
    setValidationWarnings([]);

    const payload = buildPayload();

    if (submitForReview) {
      setSubmittingReview(true);
    } else {
      setLoading(true);
    }

    try {
      let savedListing;
      if (isEdit) {
        const res = await api.put(`/api/listings/${id}`, payload);
        savedListing = res.data.listing;
        toast.success('Listing updated successfully!');
      } else {
        const res = await api.post('/api/listings', payload);
        savedListing = res.data.listing;
        toast.success('Listing created successfully!');
      }

      if (submitForReview && savedListing?.id) {
        toast.info('Triggering AI compliance evaluation with Gemini...');
        const reviewRes = await api.post(`/api/listings/${savedListing.id}/review`);
        toast.success('AI Review completed!');
        navigate(`/reviews/${reviewRes.data.review.id}`);
      } else {
        navigate('/listings');
      }
    } catch (err) {
      if (err.response?.data?.errors) {
        setValidationErrors(err.response.data.errors);
        setValidationWarnings(err.response.data.warnings || []);
        toast.error('Listing failed deterministic validation.');
      } else {
        toast.error(err.message || 'Operation failed');
      }
    } finally {
      setLoading(false);
      setSubmittingReview(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <Link
            to="/listings"
            className="p-2 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-slate-800 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {isEdit ? 'Edit Listing' : 'Create New Listing'}
            </h1>
            <p className="text-sm text-slate-500">
              Provide accurate product attributes and truthful claims.
            </p>
          </div>
        </div>
      </div>

      {/* Validation Alert Box if any errors */}
      {Object.keys(validationErrors).length > 0 && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 text-xs space-y-1">
          <div className="flex items-center gap-1.5 font-bold">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            Validation Engine Identified Requirements Not Met:
          </div>
          <ul className="list-disc list-inside space-y-0.5 pl-2">
            {Object.entries(validationErrors).map(([f, msg]) => (
              <li key={f}>
                <span className="font-semibold capitalize">{f}</span>: {msg}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings Banner if any */}
      {validationWarnings.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-1">
          <div className="flex items-center gap-1.5 font-bold">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            Validation Notices / Duplicate Warnings:
          </div>
          <ul className="list-disc list-inside space-y-0.5 pl-2">
            {validationWarnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={(e) => handleSubmit(e, false)} className="space-y-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-5">
          {/* Title */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Product Title <span className="text-rose-500">*</span>
              </label>
              <span
                className={`text-[11px] ${
                  formData.title.length > 150 ? 'text-rose-600 font-bold' : 'text-slate-400'
                }`}
              >
                {formData.title.length}/150 characters
              </span>
            </div>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="e.g. Ergonomic Office Chair with Adjustable Lumbar Support"
              className={`w-full text-sm bg-slate-50 border rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-slate-800 ${
                validationErrors.title
                  ? 'border-rose-400 focus:border-rose-500'
                  : 'border-slate-200 focus:border-indigo-500'
              }`}
            />
            {validationErrors.title && (
              <p className="text-[11px] text-rose-600 mt-1">{validationErrors.title}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Listing Description <span className="text-rose-500">*</span>
              </label>
              <span
                className={`text-[11px] ${
                  formData.description.length > 5000 ? 'text-rose-600 font-bold' : 'text-slate-400'
                }`}
              >
                {formData.description.length}/5000 characters
              </span>
            </div>
            <textarea
              name="description"
              rows={5}
              value={formData.description}
              onChange={handleChange}
              placeholder="Comprehensive product specifications, dimensions, materials, contents, and factual details..."
              className={`w-full text-sm bg-slate-50 border rounded-xl p-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-slate-800 ${
                validationErrors.description
                  ? 'border-rose-400 focus:border-rose-500'
                  : 'border-slate-200 focus:border-indigo-500'
              }`}
            />
            {validationErrors.description && (
              <p className="text-[11px] text-rose-600 mt-1">{validationErrors.description}</p>
            )}
          </div>

          {/* Category, Type, Seller */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
                Category <span className="text-rose-500">*</span>
              </label>
              <select
                name="category"
                value={formData.category}
                onChange={handleChange}
                className={`w-full text-sm bg-slate-50 border rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-slate-800 ${
                  validationErrors.category
                    ? 'border-rose-400 focus:border-rose-500'
                    : 'border-slate-200 focus:border-indigo-500'
                }`}
              >
                <option value="">Select a category...</option>
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              {validationErrors.category && (
                <p className="text-[11px] text-rose-600 mt-1">{validationErrors.category}</p>
              )}
            </div>

            <div>
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
                Listing Type
              </label>
              <select
                name="listing_type"
                value={formData.listing_type}
                onChange={handleChange}
                className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:border-indigo-500 text-slate-800"
              >
                <option value="Product">Physical Product</option>
                <option value="Service">Professional Service</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
                Seller / Vendor <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                name="seller"
                value={formData.seller}
                onChange={handleChange}
                placeholder="e.g. Apex Global Brands"
                className={`w-full text-sm bg-slate-50 border rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-slate-800 ${
                  validationErrors.seller
                    ? 'border-rose-400 focus:border-rose-500'
                    : 'border-slate-200 focus:border-indigo-500'
                }`}
              />
              {validationErrors.seller && (
                <p className="text-[11px] text-rose-600 mt-1">{validationErrors.seller}</p>
              )}
            </div>
          </div>

          {/* Price & Currency */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
                Price Amount <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                name="price"
                value={formData.price}
                onChange={handleChange}
                placeholder="e.g. 49.99"
                className={`w-full text-sm bg-slate-50 border rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-slate-800 ${
                  validationErrors.price
                    ? 'border-rose-400 focus:border-rose-500'
                    : 'border-slate-200 focus:border-indigo-500'
                }`}
              />
              {validationErrors.price && (
                <p className="text-[11px] text-rose-600 mt-1">{validationErrors.price}</p>
              )}
            </div>

            <div>
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
                Currency
              </label>
              <select
                name="currency"
                value={formData.currency}
                onChange={handleChange}
                className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:border-indigo-500 text-slate-800"
              >
                {currencies.map((curr) => (
                  <option key={curr} value={curr}>
                    {curr}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1">
              Tags (Optional comma-separated)
            </label>
            <input
              type="text"
              name="tags"
              value={formData.tags}
              onChange={handleChange}
              placeholder="e.g. ergonomic, home office, breathable, mesh"
              className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800"
            />
          </div>

          {/* Attributes Key-Value Builder */}
          <div className="pt-2 border-t border-slate-100">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Product Attributes & Technical Specifications
              </label>
              <button
                type="button"
                onClick={addAttributeRow}
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Attribute
              </button>
            </div>

            <div className="space-y-2">
              {formData.attributes.map((attr, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Specification name (e.g. Material)"
                    value={attr.key}
                    onChange={(e) => handleAttributeChange(idx, 'key', e.target.value)}
                    className="w-1/2 text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500 text-slate-800"
                  />
                  <input
                    type="text"
                    placeholder="Specification value (e.g. Breathable Mesh)"
                    value={attr.value}
                    onChange={(e) => handleAttributeChange(idx, 'value', e.target.value)}
                    className="w-1/2 text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500 text-slate-800"
                  />
                  {formData.attributes.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeAttributeRow(idx)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3">
          <Link
            to="/listings"
            className="px-5 py-2.5 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 text-sm font-semibold transition"
          >
            Cancel
          </Link>

          <button
            type="submit"
            disabled={loading || submittingReview}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-900 text-white text-sm font-semibold transition disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Draft
          </button>

          <button
            type="button"
            onClick={(e) => handleSubmit(e, true)}
            disabled={loading || submittingReview}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-md shadow-indigo-100 transition disabled:opacity-50"
          >
            {submittingReview ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Validating & Reviewing...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Save & Run AI Review
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
