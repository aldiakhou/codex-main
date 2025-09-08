import React from 'react';
import ChatMessages from '../ChatMessages';
import ChatInterface from '../ChatInterface';
import ErrorBanner from '../ErrorBanner';
import { useBackend } from '../../contexts/BackendContext';
import ChatToolCalls from '../ChatToolCalls';

const ChatWorkspace: React.FC = () => {
  const { status, lastError } = useBackend();
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between p-6 pb-2">
        <h1 className="text-2xl font-bold">Chat</h1>
        <div className="flex items-center gap-3">
          <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-sm" onClick={()=>window.aiw.getHistory()}>Load History</button>
          <div className="text-sm text-[var(--text-secondary)]">Status: {status}</div>
        </div>
      </div>
      <div className="px-6">
        <ErrorBanner message={lastError || null} />
        <ChatToolCalls />
        <ChatMessages />
      </div>
      <div className="mt-auto">
        <ChatInterface />
      </div>
    </div>
  );
};

export default ChatWorkspace;
