import React, { useState, useEffect, useRef } from 'react';
import { flameApi } from '../../services/flameApi';

export function KnowledgeManagementModal({ isOpen, onClose, onDocumentIngested }) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'manifest' | 'verify'
  
  // Upload State
  const [selectedFile, setSelectedFile] = useState(null);
  const [title, setTitle] = useState('');
  const [investigation, setInvestigation] = useState('');
  const [attribution, setAttribution] = useState('');
  const [notes, setNotes] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const fileInputRef = useRef(null);

  // Manifest / Knowledge Base Stats State
  const [kbStatus, setKbStatus] = useState(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);

  // Test Retrieval State
  const [testQuery, setTestQuery] = useState('PMMA flame spread microgravity');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [searchError, setSearchError] = useState(null);

  // Load KB status whenever modal opens or tab changes to manifest
  const loadStatus = async () => {
    setIsLoadingStatus(true);
    try {
      const data = await flameApi.getKnowledgeBaseOverview();
      setKbStatus(data);
    } catch (err) {
      console.error('Failed to load KB status:', err);
    } finally {
      setIsLoadingStatus(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadStatus();
      setUploadError(null);
      setUploadResult(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      if (!title) {
        setTitle(file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' '));
      }
      setUploadError(null);
      setUploadResult(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
      if (!title) {
        setTitle(file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' '));
      }
      setUploadError(null);
      setUploadResult(null);
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a document or dataset file to ingest.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      if (title.trim()) formData.append('title', title.trim());
      if (investigation.trim()) formData.append('investigation', investigation.trim());
      if (attribution.trim()) formData.append('source_attribution', attribution.trim());
      if (notes.trim()) formData.append('notes', notes.trim());

      const res = await flameApi.uploadKnowledgeDocument(formData);
      setUploadResult(res);
      setSelectedFile(null);
      setTitle('');
      setInvestigation('');
      setAttribution('');
      setNotes('');
      if (fileInputRef.current) fileInputRef.current.value = '';

      // Reload manifest status
      await loadStatus();
      if (onDocumentIngested) onDocumentIngested(res);
    } catch (err) {
      setUploadError(err.message || 'Failed to upload document');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!window.confirm('Are you sure you want to remove this document and its indexed records from the RAG store?')) {
      return;
    }
    try {
      await flameApi.deleteKnowledgeDocument(docId);
      await loadStatus();
    } catch (err) {
      alert(`Failed to delete document: ${err.message}`);
    }
  };

  const handleTestSearch = async (e) => {
    e?.preventDefault();
    if (!testQuery.trim()) return;

    setIsSearching(true);
    setSearchError(null);
    setSearchResults(null);

    try {
      const res = await flameApi.testKnowledgeSearch(testQuery.trim(), 4);
      setSearchResults(res);
    } catch (err) {
      setSearchError(err.message || 'Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div 
        className="w-full max-w-4xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-orange-100 border border-orange-200 flex items-center justify-center text-orange-600">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900 tracking-tight">
                  Dynamic RAG Knowledge Ingestion
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                  Live Indexing
                </span>
              </div>
              <p className="text-xs text-slate-500 font-mono">
                Import research papers, telemetry CSVs, and datasets directly into the active knowledge store
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-lg border border-slate-200 text-slate-400 hover:text-slate-700 hover:bg-slate-100 flex items-center justify-center transition-colors cursor-pointer text-sm"
            title="Close dialog"
          >
            ✕
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="px-6 py-2 border-b border-slate-200 bg-white flex items-center gap-2 text-xs font-mono">
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer font-medium ${
              activeTab === 'upload'
                ? 'bg-orange-500 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            1. Ingest New Document
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('manifest');
              loadStatus();
            }}
            className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer font-medium flex items-center gap-1.5 ${
              activeTab === 'manifest'
                ? 'bg-orange-500 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            2. Active Knowledge Base
            {kbStatus && (
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${activeTab === 'manifest' ? 'bg-orange-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
                {kbStatus.total_records}
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('verify')}
            className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer font-medium ${
              activeTab === 'verify'
                ? 'bg-orange-500 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            3. Verify Retrieval & Citations
          </button>
        </div>

        {/* Tab 1: Upload / Ingest File */}
        {activeTab === 'upload' && (
          <div className="p-6 overflow-y-auto space-y-5">
            <form onSubmit={handleUploadSubmit} className="space-y-4">
              {/* Dropzone */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                  selectedFile
                    ? 'border-orange-500 bg-orange-50/30'
                    : 'border-slate-300 hover:border-orange-400 bg-slate-50/50 hover:bg-orange-50/10'
                }`}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".csv,.tsv,.xlsx,.xls,.pdf,.txt,.md,.json"
                  className="hidden"
                />

                <div className="w-12 h-12 mx-auto rounded-full bg-orange-100 text-orange-600 flex items-center justify-center mb-2">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>

                {selectedFile ? (
                  <div>
                    <span className="font-mono text-sm font-bold text-slate-900 block">
                      {selectedFile.name}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">
                      {(selectedFile.size / 1024).toFixed(1)} KB • Ready for extraction
                    </span>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-semibold text-slate-800">
                      Drag and drop your file here, or <span className="text-orange-600 underline">browse</span>
                    </p>
                    <p className="text-xs text-slate-500 font-mono mt-1">
                      Supported formats: CSV, TSV, XLSX, XLS, PDF, TXT, Markdown, JSON (max 25 MB)
                    </p>
                  </div>
                )}
              </div>

              {/* Metadata Fields */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
                <div className="space-y-1">
                  <label className="text-slate-700 font-semibold block">Document Title</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Saffire-IV Flammability Summary"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-900 focus:outline-none focus:border-orange-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-slate-700 font-semibold block">Flight Investigation / Project</label>
                  <input
                    type="text"
                    value={investigation}
                    onChange={(e) => setInvestigation(e.target.value)}
                    placeholder="e.g. BASS-II, Saffire-III, ISS CIR"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-900 focus:outline-none focus:border-orange-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-slate-700 font-semibold block">Source Attribution / Institution</label>
                  <input
                    type="text"
                    value={attribution}
                    onChange={(e) => setAttribution(e.target.value)}
                    placeholder="e.g. NASA Glenn Research Center"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-900 focus:outline-none focus:border-orange-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-slate-700 font-semibold block">Notes & Tags</label>
                  <input
                    type="text"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="e.g. High oxygen 30% PMMA ignition run"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-900 focus:outline-none focus:border-orange-500"
                  />
                </div>
              </div>

              {/* Status / Messages */}
              {uploadError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs font-mono text-rose-700 flex items-center gap-2">
                  <span className="text-rose-500 font-bold">✕ Error:</span> {uploadError}
                </div>
              )}

              {uploadResult && (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs font-mono text-emerald-800 space-y-1.5">
                  <div className="flex items-center gap-2 font-bold text-emerald-900">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    {uploadResult.message || 'Document indexed successfully!'}
                  </div>
                  <div className="text-[11px] text-emerald-700">
                    Document ID: <code className="bg-emerald-100 px-1 py-0.5 rounded">{uploadResult.document_id}</code> • 
                    Records Indexed: <strong>{uploadResult.record_count}</strong> • 
                    Total Store Records: <strong>{uploadResult.total_knowledge_store_records}</strong>
                  </div>
                  <div className="pt-1">
                    <button
                      type="button"
                      onClick={() => {
                        setActiveTab('verify');
                        setTestQuery(uploadResult.title || 'microgravity');
                        handleTestSearch();
                      }}
                      className="text-emerald-800 underline font-bold hover:text-emerald-900 cursor-pointer"
                    >
                      → Verify retrieval with a test query now
                    </button>
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="submit"
                  disabled={!selectedFile || isUploading}
                  className={`px-5 py-2.5 rounded-xl font-mono text-xs font-bold transition-all cursor-pointer flex items-center gap-2 ${
                    !selectedFile || isUploading
                      ? 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
                      : 'bg-orange-500 hover:bg-orange-600 text-white shadow-xs'
                  }`}
                >
                  {isUploading ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Parsing & Indexing into RAG Store...
                    </>
                  ) : (
                    'Ingest into Active Knowledge Base →'
                  )}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Tab 2: Manifest & Active Store Stats */}
        {activeTab === 'manifest' && (
          <div className="p-6 overflow-y-auto space-y-5">
            {isLoadingStatus ? (
              <div className="py-12 text-center text-xs font-mono text-slate-500">
                Loading Knowledge Base status...
              </div>
            ) : kbStatus ? (
              <div className="space-y-4">
                {/* Stats Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center font-mono">
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                    <span className="text-[10px] text-slate-500 uppercase block">Total Records</span>
                    <span className="text-lg font-bold text-slate-900">{kbStatus.total_records}</span>
                  </div>
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                    <span className="text-[10px] text-slate-500 uppercase block">Canonical Flight</span>
                    <span className="text-lg font-bold text-slate-900">{kbStatus.canonical_records}</span>
                  </div>
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                    <span className="text-[10px] text-slate-500 uppercase block">Uploaded Records</span>
                    <span className="text-lg font-bold text-orange-600">{kbStatus.uploaded_records}</span>
                  </div>
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                    <span className="text-[10px] text-slate-500 uppercase block">Uploaded Docs</span>
                    <span className="text-lg font-bold text-slate-900">{kbStatus.uploaded_documents_count}</span>
                  </div>
                </div>

                {/* Uploaded Documents List */}
                <div className="space-y-2">
                  <h3 className="text-xs font-mono font-bold text-slate-800 uppercase tracking-wider">
                    Uploaded Document Index ({kbStatus.documents?.length || 0})
                  </h3>

                  {(!kbStatus.documents || kbStatus.documents.length === 0) ? (
                    <div className="p-6 border border-dashed border-slate-200 rounded-xl text-center text-xs font-mono text-slate-500">
                      No custom documents uploaded yet. The active store currently contains {kbStatus.canonical_records} canonical NASA flight records (BASS-II, Saffire-III, Cygnus telemetry).
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-72 overflow-y-auto">
                      {kbStatus.documents.map((doc) => (
                        <div
                          key={doc.document_id}
                          className="bg-white border border-slate-200 rounded-xl p-3 flex items-center justify-between gap-3 text-xs font-mono"
                        >
                          <div className="space-y-0.5 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-900 truncate">{doc.title}</span>
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                                {doc.record_count} chunks
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-500 truncate">
                              File: {doc.filename} • Investigation: {doc.investigation_name} • {(doc.file_size_bytes / 1024).toFixed(1)} KB
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() => handleDeleteDocument(doc.document_id)}
                            className="px-2.5 py-1 rounded border border-rose-200 text-rose-600 hover:bg-rose-50 text-[11px] font-mono transition-colors cursor-pointer shrink-0"
                            title="Delete this document and its records from the index"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* Tab 3: Retrieval Verification Test */}
        {activeTab === 'verify' && (
          <div className="p-6 overflow-y-auto space-y-4">
            <form onSubmit={handleTestSearch} className="space-y-3">
              <label className="text-xs font-mono text-slate-700 font-semibold block">
                Test Live Hybrid RRF Retrieval Against Store:
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  placeholder="Enter scientific keywords or uploaded document terms..."
                  className="flex-1 px-3 py-2 rounded-xl border border-slate-200 bg-white text-xs font-mono text-slate-900 focus:outline-none focus:border-orange-500"
                />
                <button
                  type="submit"
                  disabled={isSearching || !testQuery.trim()}
                  className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white font-mono text-xs font-bold rounded-xl transition-all cursor-pointer shadow-xs disabled:opacity-50"
                >
                  {isSearching ? 'Searching...' : 'Search Index →'}
                </button>
              </div>
            </form>

            {searchError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs font-mono text-rose-700">
                {searchError}
              </div>
            )}

            {searchResults && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between text-xs font-mono text-slate-500">
                  <span>Found {searchResults.total_found} verified candidate records</span>
                  <span>Mode: Hybrid BM25 + Vector</span>
                </div>

                <div className="space-y-2.5 max-h-80 overflow-y-auto">
                  {searchResults.citations?.map((cit, idx) => (
                    <div
                      key={cit.record_id || idx}
                      className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono space-y-1.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-bold text-slate-900 truncate">
                          {cit.title || cit.dataset_name || cit.record_id}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-100 text-orange-800 font-bold shrink-0">
                          {cit.record_id}
                        </span>
                      </div>

                      <p className="text-[11px] text-slate-600 leading-relaxed font-sans line-clamp-3">
                        {cit.evidence_text || cit.summary_text || cit.description || 'Verified experimental record'}
                      </p>

                      <div className="flex flex-wrap items-center gap-2 pt-1 text-[10px] text-slate-500">
                        {cit.investigation && (
                          <span className="bg-white px-1.5 py-0.5 rounded border border-slate-200">
                            Inv: {cit.investigation}
                          </span>
                        )}
                        {cit.fuel_material && (
                          <span className="bg-white px-1.5 py-0.5 rounded border border-slate-200">
                            Fuel: {cit.fuel_material}
                          </span>
                        )}
                        {cit.oxygen_percent !== undefined && (
                          <span className="bg-white px-1.5 py-0.5 rounded border border-slate-200">
                            O2: {cit.oxygen_percent}%
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
