import React, { useState } from 'react';
import { X, Upload, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import api from '../api/client';
import { useToast } from '../context/ToastContext';

export const CsvImportModal = ({ isOpen, onClose, onSuccess }) => {
  const [csvText, setCsvText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const toast = useToast();

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        setCsvText(event.target.result);
      };
      reader.readAsText(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!csvText.trim()) {
      toast.error('Please upload a CSV file or paste CSV content.');
      return;
    }

    setLoading(true);
    setImportResult(null);

    try {
      const response = await api.post('/api/batch/import-csv', { csv_content: csvText });
      setImportResult(response.data);
      toast.success(`Successfully imported ${response.data.imported_count} listings!`);
      if (onSuccess) onSuccess();
    } catch (err) {
      toast.error(err.message || 'CSV import failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <Upload className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">Batch CSV Import</h3>
              <p className="text-xs text-slate-500">Import multiple product listings into the database</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div>
            <span className="text-xs font-medium text-slate-600">
              Upload CSV file or paste standard CSV content:
            </span>
          </div>

          <div className="border-2 border-dashed border-slate-200 rounded-xl p-4 text-center hover:border-indigo-300 transition-colors">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
              id="csv-file-input"
            />
            <label
              htmlFor="csv-file-input"
              className="cursor-pointer flex flex-col items-center gap-1.5"
            >
              <FileText className="w-6 h-6 text-slate-400" />
              <span className="text-xs font-semibold text-slate-700">
                {selectedFile ? selectedFile.name : 'Click to select .csv file'}
              </span>
              <span className="text-[11px] text-slate-400">or paste text below</span>
            </label>
          </div>

          <div>
            <textarea
              rows={8}
              value={csvText}
              onChange={(e) => setCsvText(e.target.value)}
              placeholder="title,description,category,price,currency,listing_type,seller,tags,attributes..."
              className="w-full font-mono text-xs bg-slate-50 border border-slate-200 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800"
            />
          </div>

          {importResult && (
            <div className="p-4 rounded-xl border bg-slate-50 space-y-2 text-xs">
              <div className="flex items-center justify-between font-semibold">
                <span className="flex items-center gap-1.5 text-emerald-700">
                  <CheckCircle2 className="w-4 h-4" />
                  Imported: {importResult.imported_count}
                </span>
                <span className="flex items-center gap-1.5 text-rose-700">
                  <AlertCircle className="w-4 h-4" />
                  Errors: {importResult.errors_count}
                </span>
              </div>
              {importResult.errors && importResult.errors.length > 0 && (
                <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
                  {importResult.errors.map((err, i) => (
                    <div key={i} className="text-[11px] text-rose-600 bg-rose-50 p-1.5 rounded">
                      Row {err.row} ({err.title}): {JSON.stringify(err.errors)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-end gap-3 bg-slate-50/50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800"
          >
            Close
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white transition shadow-sm disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Validating & Importing...
              </>
            ) : (
              'Import Listings'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
