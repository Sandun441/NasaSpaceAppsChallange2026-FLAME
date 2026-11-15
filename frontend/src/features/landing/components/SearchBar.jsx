import React from 'react';
import { ResearchPromptBar } from '../../../components/common/ResearchPromptBar';

/**
 * SearchBar: Reconciled legacy entry point that delegates to the shared,
 * live AI research prompt bar.
 */
export function SearchBar({ onActionTriggered, className = '' }) {
  return (
    <div className={`w-full max-w-4xl mx-auto ${className}`}>
      <ResearchPromptBar
        initialWorkspace="auto"
        onActionTriggered={onActionTriggered}
        renderInlineResults={true}
      />
    </div>
  );
}
