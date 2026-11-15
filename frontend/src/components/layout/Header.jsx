import React, { useState, useRef, useEffect } from 'react';
import { RESEARCH_TOOLS } from '../../lib/constants';

function ToolIcon({ icon, className = 'w-4 h-4' }) {
  switch (icon) {
    case 'Chart':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
        </svg>
      );
    case 'Scale':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
        </svg>
      );
    case 'Matrix':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7C5 4 4 5 4 7zm4 4h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15h.01" />
        </svg>
      );
    case 'Target':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="9" strokeWidth="2" />
          <circle cx="12" cy="12" r="5" strokeWidth="2" />
          <circle cx="12" cy="12" r="1" fill="currentColor" />
        </svg>
      );
    case 'Shield':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      );
    case 'Globe':
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" strokeWidth="2" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
        </svg>
      );
    default:
      return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      );
  }
}

export function Header({
  activeTab = 'home',
  onSelectTab,
  onOpenDashboard,
  onOpenKnowledgeModal,
  onToggleMenu,
  apiStatus,
}) {
  const [toolsDropdownOpen, setToolsDropdownOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setToolsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isConnected = apiStatus?.isConnected;
  const isConnecting = apiStatus?.isConnecting;

  const toolIds = RESEARCH_TOOLS.map((t) => t.id);
  const isToolActive = toolIds.includes(activeTab);
  const activeToolObj = RESEARCH_TOOLS.find((t) => t.id === activeTab);

  return (
    <header className="max-w-6xl w-full mx-auto flex items-center justify-between pb-3 sm:pb-5 border-b border-slate-200 relative z-40">
      {/* Brand & Logo */}
      <div
        className="flex items-center gap-2.5 cursor-pointer group"
        onClick={() => onSelectTab && onSelectTab('home')}
      >
        <div className="w-7 h-7 rounded-lg bg-orange-50 border border-orange-200 text-orange-600 flex items-center justify-center font-bold text-xs tracking-wider shadow-xs group-hover:bg-orange-500 group-hover:text-white transition-all">
          Δ
        </div>
        <div className="flex items-baseline gap-2">
          <span className="font-semibold text-base tracking-tight text-slate-900 group-hover:text-orange-600 transition-colors">
            FLAME
          </span>
          <span className="text-xs text-slate-500 font-mono hidden md:inline">
            NASA Microgravity Research Intelligence
          </span>
        </div>
      </div>

      {/* Simplified, Clean Navigation Menu */}
      <nav className="hidden md:flex items-center gap-1.5 text-xs">
        {/* Home */}
        <button
          type="button"
          onClick={() => onSelectTab && onSelectTab('home')}
          className={`px-3 py-1.5 rounded-lg transition-all duration-150 flex items-center gap-1.5 font-medium cursor-pointer ${
            activeTab === 'home'
              ? 'bg-slate-100 text-slate-900 shadow-xs border border-slate-200'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/60'
          }`}
        >
          <span>Home</span>
          {activeTab === 'home' && (
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500 ml-0.5 animate-pulse" />
          )}
        </button>

        {/* Research Tools Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setToolsDropdownOpen(!toolsDropdownOpen)}
            className={`px-3 py-1.5 rounded-lg transition-all duration-150 flex items-center gap-1.5 font-medium cursor-pointer ${
              isToolActive
                ? 'bg-slate-100 text-slate-900 shadow-xs border border-slate-200'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/60'
            }`}
          >
            <span>Research Tools</span>
            {isToolActive && (
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-orange-50 text-orange-600 font-mono border border-orange-200">
                {activeToolObj?.title || 'Active'}
              </span>
            )}
            <svg
              className={`w-3.5 h-3.5 transition-transform duration-200 opacity-60 ${
                toolsDropdownOpen ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Dropdown Menu Popover */}
          {toolsDropdownOpen && (
            <div className="absolute top-full left-0 mt-2 w-72 p-2 rounded-xl bg-white border border-slate-200 shadow-xl flex flex-col gap-1 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="px-2.5 py-1 text-[10px] font-mono uppercase tracking-wider text-slate-500 border-b border-slate-100 mb-1 flex items-center justify-between">
                <span>Specialist Research Tools</span>
                <span className="text-orange-600 font-semibold">6 Workspaces</span>
              </div>

              {RESEARCH_TOOLS.map((tool) => {
                const isActive = activeTab === tool.id;
                return (
                  <button
                    key={tool.id}
                    type="button"
                    onClick={() => {
                      if (onSelectTab) onSelectTab(tool.id);
                      setToolsDropdownOpen(false);
                    }}
                    className={`w-full text-left p-2 rounded-lg transition-all duration-150 flex items-start gap-2.5 cursor-pointer ${
                      isActive
                        ? 'bg-slate-100 text-slate-900 border border-slate-200'
                        : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900'
                    }`}
                  >
                    <div className="p-1 rounded bg-slate-50 border border-slate-200 text-orange-500 mt-0.5">
                      <ToolIcon icon={tool.icon} className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-xs truncate">{tool.title}</span>
                        {isActive && <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />}
                      </div>
                      <p className="text-[11px] text-slate-500 truncate">{tool.tag}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </nav>

      {/* Header Actions */}
      <div className="flex items-center gap-2">
        {/* Live API Telemetry Pill */}
        {apiStatus && (
          <button
            onClick={() => onSelectTab && onSelectTab('dataset-explorer')}
            className={`hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-[11px] font-mono transition-colors cursor-pointer ${
              isConnected
                ? 'bg-emerald-500 text-white border-emerald-500 hover:bg-emerald-600 shadow-xs'
                : isConnecting
                ? 'bg-amber-50 text-amber-700 border-amber-200'
                : 'bg-rose-50 text-rose-700 border-rose-200'
            }`}
            title="Click to open Live Dataset Explorer"
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isConnected
                  ? 'bg-white animate-pulse'
                  : isConnecting
                  ? 'bg-amber-500 animate-ping'
                  : 'bg-rose-500'
              }`}
            />
            <span>
              {isConnected
                ? `Live API (${apiStatus.datasetCount ?? 11})`
                : isConnecting
                ? 'Connecting...'
                : 'API Offline'}
            </span>
          </button>
        )}

        {/* Knowledge Base Import Button */}
        {onOpenKnowledgeModal && (
          <button
            type="button"
            onClick={onOpenKnowledgeModal}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 text-[11px] font-mono transition-colors cursor-pointer shadow-xs"
            title="Open Dynamic RAG Knowledge Base & File Ingestion"
          >
            <svg className="w-3.5 h-3.5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span className="font-semibold">Import Data</span>
          </button>
        )}

        {/* Compact Overflow Menu Toggle */}
        {onToggleMenu && (
          <button
            type="button"
            onClick={onToggleMenu}
            className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer"
            title="Open platform menu"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}

        {/* Mobile Menu Toggle Button */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer"
          aria-label="Toggle navigation menu"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {mobileMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Dropdown Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 mt-3 p-4 bg-white border border-slate-200 rounded-xl shadow-xl flex flex-col gap-2 text-xs text-slate-700 z-50">
          <div className="text-[11px] font-mono text-slate-500 uppercase tracking-wider pb-1 border-b border-slate-100 flex items-center justify-between">
            <span>Navigation</span>
            {apiStatus && (
              <span className={`text-[10px] ${isConnected ? 'text-emerald-600' : 'text-rose-600'}`}>
                ● {isConnected ? 'FastAPI Connected' : 'FastAPI Offline'}
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={() => {
              if (onSelectTab) onSelectTab('home');
              setMobileMenuOpen(false);
            }}
            className={`py-2 px-3 rounded-lg text-left transition-colors flex items-center justify-between cursor-pointer ${
              activeTab === 'home' ? 'bg-slate-100 text-slate-900 font-medium border border-slate-200' : 'hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <span>Home (AI Assistant)</span>
            </div>
            {activeTab === 'home' && <span className="text-[10px] text-orange-600 font-mono">Active</span>}
          </button>

          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider pt-2 pb-1 border-t border-slate-100">
            Research Tools
          </div>

          {RESEARCH_TOOLS.map((tool) => {
            const isActive = activeTab === tool.id;
            return (
              <button
                key={tool.id}
                type="button"
                onClick={() => {
                  if (onSelectTab) onSelectTab(tool.id);
                  setMobileMenuOpen(false);
                }}
                className={`py-2 px-3 rounded-lg text-left transition-colors flex items-center justify-between cursor-pointer ${
                  isActive ? 'bg-slate-100 text-slate-900 font-medium border border-slate-200' : 'hover:bg-slate-50'
                }`}
              >
                <span>{tool.title}</span>
                {isActive && <span className="text-[10px] text-orange-600 font-mono">Active</span>}
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
}
