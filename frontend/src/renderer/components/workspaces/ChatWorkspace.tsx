import React from 'react';
import ChatMessages from '../ChatMessages';
import ChatInterface from '../ChatInterface';
import ChatControls from '../ChatControls';
import ErrorBanner from '../ErrorBanner';
import { useBackend } from '../../contexts/BackendContext';
import { useBackend } from '../../contexts/BackendContext';

const ChatWorkspace: React.FC = () => {
  const { status, lastError } = useBackend();
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between p-6 pb-2">
        <h1 className="text-2xl font-bold">Chat</h1>
        <div className="text-sm text-[var(--text-secondary)]">Status: {status}</div>
      </div>
      <div className="px-6">
        <ErrorBanner message={lastError || null} />
        <ChatControls />
        <ChatMessages />
      </div>
      <div className="mt-auto">
        <ChatInterface />
      </div>
    </div>
  );
};

export default ChatWorkspace;
