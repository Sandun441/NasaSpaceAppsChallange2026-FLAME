import React from 'react';
import { ScientificAiAssistant } from '../../ai-assistant';

export function HeroSection({
  onSelectTab,
  initialContext,
  messages,
  setMessages,
  inputQuery,
  setInputQuery,
  activeFinding,
  setActiveFinding,
  activeEarthEvidence,
  setActiveEarthEvidence,
}) {
  return (
    <section className="text-center pt-2 pb-4 max-w-5xl mx-auto px-2 sm:px-4">
      <ScientificAiAssistant
        isHomepage={true}
        onSelectTab={onSelectTab}
        initialContext={initialContext}
        messages={messages}
        setMessages={setMessages}
        inputQuery={inputQuery}
        setInputQuery={setInputQuery}
        activeFinding={activeFinding}
        setActiveFinding={setActiveFinding}
        activeEarthEvidence={activeEarthEvidence}
        setActiveEarthEvidence={setActiveEarthEvidence}
      />
    </section>
  );
}
