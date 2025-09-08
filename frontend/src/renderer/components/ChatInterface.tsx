import React, { useState } from 'react';
import { useBackend } from '../contexts/BackendContext';

const ChatInterface: React.FC = () => {
  const [message, setMessage] = useState('');
  const { status, userTurn, login, start, logs } = useBackend();
  const connected = status === 'connected';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = message.trim();
    if (!text) return;
    setMessage('');
    await userTurn(text);
  };

  return (
    <div className="bg-[var(--bg-primary)] border-t border-[var(--border)] p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-2 text-sm text-[var(--text-secondary)]">
          <div className="flex items-center gap-2">
            <span className={`inline-block w-2.5 h-2.5 rounded-full ${connected ? 'bg-green-500' : status === 'connecting' ? 'bg-yellow-500 animate-pulse' : status === 'error' ? 'bg-red-500' : 'bg-gray-500'}`} />
            <span>{status}</span>
          </div>
          <div className="flex items-center gap-2">
            {status !== 'connected' && (
              <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={() => start()}>Start</button>
            )}
            <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={() => login()}>Login</button>
          </div>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="relative">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={connected ? 'Delegate a task to Nexus AI...' : 'Starting backend...'}
              className="w-full bg-[var(--bg-tertiary)] rounded-lg py-3 pl-4 pr-12 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] border border-[var(--border)]"
              disabled={false}
            />
            <button
              type="submit"
              className="absolute inset-y-0 right-0 flex items-center pr-4 text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors disabled:opacity-50"
              disabled={!connected}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
              </svg>
            </button>
          </div>
        </form>
        {/* Log output (dev) */}
        <div className="mt-2 text-xs text-[var(--text-tertiary)] max-h-40 overflow-auto mono">
          {logs.slice(-6).map((l, i) => (
            <div key={i}>{l}</div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
