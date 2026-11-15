import React, { useState } from 'react';
import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';
import { MenuDrawer } from '../components/layout/MenuDrawer';
import { LandingPage } from '../features/landing';
import { DatasetExplorer } from '../features/dataset-explorer';
import { ExperimentComparison } from '../features/experiment-comparison';
import { ResearchGapDetection } from '../features/gap-detection';
import { EquipmentResearch } from '../features/equipment-research';
import { EarthApplications } from '../features/earth-applications';
import { PredictiveModelingExtraction } from '../features/modeling-extraction';
import { KnowledgeManagementModal } from '../features/knowledge-import';
import { useApiStatus } from '../hooks/useApiStatus';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [tabContext, setTabContext] = useState(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isKnowledgeModalOpen, setIsKnowledgeModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Persistent conversational AI assistant state across normal workspace navigation (Step 2 & 5)
  const [assistantMessages, setAssistantMessages] = useState([]);
  const [assistantInput, setAssistantInput] = useState('');
  const [activeFinding, setActiveFinding] = useState(null);
  const [activeEarthEvidence, setActiveEarthEvidence] = useState(null);

  // Global live API status hook
  const apiStatus = useApiStatus();

  // Smooth scroll to top when changing tabs, preserving optional cross-module context
  const handleSelectTab = (tabId, contextData = null) => {
    // If incoming navigation targets 'ai-assistant', route seamlessly to 'home' where the assistant lives
    const effectiveTab = tabId === 'ai-assistant' ? 'home' : tabId;
    setActiveTab(effectiveTab);
    setTabContext(contextData);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleOpenDashboard = () => {
    setActiveTab('gap-detection');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    showToast('Switched to Research Gap Detection dashboard view');
  };

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3200);
  };

  const knownTabs = [
    'home',
    'dataset-explorer',
    'experiment-comparison',
    'modeling-extraction',
    'gap-detection',
    'equipment-research',
    'earth-applications',
  ];

  return (
    <div className="min-h-screen bg-white text-slate-900 flex flex-col justify-between p-3 sm:p-6 md:p-8 font-sans selection:bg-orange-500/20 selection:text-orange-900 relative overflow-x-hidden">
      {/* Background Subtle Starfield / Grid Texture */}
      <div 
        className="fixed inset-0 pointer-events-none opacity-50 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:24px_24px]" 
        aria-hidden="true" 
      />

      {/* Subtle Radial Atmosphere Light */}
      <div 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-sky-500/5 blur-[140px] rounded-full pointer-events-none" 
        aria-hidden="true" 
      />

      {/* Main Layout Container */}
      <div className="relative z-10 flex flex-col min-h-screen justify-between">
        {/* Navigation Header */}
        <Header 
          activeTab={activeTab}
          onSelectTab={handleSelectTab}
          onOpenDashboard={handleOpenDashboard}
          onOpenKnowledgeModal={() => setIsKnowledgeModalOpen(true)}
          onToggleMenu={() => setIsMenuOpen(true)}
          apiStatus={apiStatus}
        />

        {/* Global Notification Toast */}
        {toastMessage && (
          <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 shadow-xl flex items-center gap-2 animate-in fade-in slide-in-from-top-2 duration-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>{toastMessage}</span>
            <button 
              onClick={() => setToastMessage(null)} 
              className="text-slate-400 hover:text-slate-700 ml-2 text-xs"
            >
              ✕
            </button>
          </div>
        )}

        {/* Dynamic View Body */}
        <div className="flex-1 my-4">
          {activeTab === 'home' && (
            <LandingPage 
              onOpenDashboard={handleOpenDashboard} 
              onSelectTab={handleSelectTab}
              onOpenKnowledgeModal={() => setIsKnowledgeModalOpen(true)}
              initialContext={tabContext}
              messages={assistantMessages}
              setMessages={setAssistantMessages}
              inputQuery={assistantInput}
              setInputQuery={setAssistantInput}
              activeFinding={activeFinding}
              setActiveFinding={setActiveFinding}
              activeEarthEvidence={activeEarthEvidence}
              setActiveEarthEvidence={setActiveEarthEvidence}
            />
          )}

          {activeTab === 'dataset-explorer' && (
            <DatasetExplorer initialContext={tabContext} />
          )}

          {activeTab === 'experiment-comparison' && (
            <ExperimentComparison initialContext={tabContext} />
          )}

          {activeTab === 'modeling-extraction' && (
            <PredictiveModelingExtraction initialContext={tabContext} onSelectTab={handleSelectTab} />
          )}

          {activeTab === 'gap-detection' && (
            <ResearchGapDetection onSelectTab={handleSelectTab} initialContext={tabContext} />
          )}

          {activeTab === 'equipment-research' && (
            <EquipmentResearch onSelectTab={handleSelectTab} initialContext={tabContext} />
          )}

          {activeTab === 'earth-applications' && (
            <EarthApplications initialContext={tabContext} onSelectTab={handleSelectTab} />
          )}

          {/* Fallback View for Unrecognized Tab */}
          {!knownTabs.includes(activeTab) && (
            <div className="p-12 text-center space-y-4 max-w-md mx-auto my-12 bg-slate-50 rounded-2xl border border-slate-200 shadow-sm">
              <div className="w-8 h-8 rounded-full bg-amber-50 text-amber-600 border border-amber-200 mx-auto flex items-center justify-center font-mono font-bold">
                !
              </div>
              <h2 className="text-sm font-semibold text-slate-900">View Not Found</h2>
              <p className="text-xs text-slate-500 font-mono">
                The requested research view &quot;{activeTab}&quot; does not exist.
              </p>
              <button
                onClick={() => handleSelectTab('home')}
                className="px-4 py-2 rounded-xl bg-slate-900 text-white font-medium text-xs hover:bg-slate-800 transition-colors cursor-pointer"
              >
                Return to Home
              </button>
            </div>
          )}
        </div>

        {/* Global Platform Footer */}
        <Footer onSelectTab={handleSelectTab} />

        {/* Full Platform Slide-Over Menu Drawer */}
        <MenuDrawer 
          isOpen={isMenuOpen} 
          onClose={() => setIsMenuOpen(false)} 
          onSelectTab={handleSelectTab}
          onOpenKnowledgeModal={() => {
            setIsMenuOpen(false);
            setIsKnowledgeModalOpen(true);
          }}
        />

        {/* Dynamic Knowledge Management Modal (Priority P2) */}
        <KnowledgeManagementModal
          isOpen={isKnowledgeModalOpen}
          onClose={() => setIsKnowledgeModalOpen(false)}
          onDocumentIngested={(res) => {
            showToast(`Document "${res.title}" indexed (${res.record_count} chunks into active RAG store)!`);
          }}
        />
      </div>
    </div>
  );
}
