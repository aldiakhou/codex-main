import React, { useMemo } from 'react';
import ChatMessages from '../ChatMessages';
import ChatInterface from '../ChatInterface';
import ErrorBanner from '../ErrorBanner';
import { useBackend } from '../../contexts/BackendContext';
import ChatToolCalls from '../ChatToolCalls';

const ChatWorkspace: React.FC = () => {
  const { status, lastError, plan } = useBackend();
  const hasPlan = useMemo(() => !!(plan && ((plan.explanation && plan.explanation.trim()) || (plan.plan && plan.plan.length))), [plan]);

  const PlanSidebar: React.FC = () => {
    if (!hasPlan) return null;
    const items = plan?.plan || [];
    const explanation = plan?.explanation || '';
    const badge = (s: string) => (
      s === 'completed' ? 'bg-green-500/20 text-green-300 border-green-500/40' :
      s === 'in_progress' ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40' :
      'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border-[var(--border)]'
    );
    return (
      <aside className="w-full lg:w-80 xl:w-96 border-l border-[var(--border)] p-4 hidden md:block">
        <div className="sticky top-0">
          <h3 className="text-lg font-semibold mb-2">Plan</h3>
          {explanation ? (
            <div className="text-sm text-[var(--text-secondary)] mb-3 whitespace-pre-wrap">{explanation}</div>
          ) : null}
          <div className="space-y-2">
            {items.length === 0 ? (
              <div className="text-sm text-[var(--text-tertiary)]">No steps yet</div>
            ) : items.map((it, idx) => (
              <div key={idx} className="border rounded px-3 py-2 bg-[var(--bg-secondary)] flex items-start gap-2">
                <span className={`text-2xs px-2 py-0.5 rounded-full border ${badge(it.status)}`}>{it.status.replace('_',' ')}</span>
                <div className="text-sm whitespace-pre-wrap flex-1">{it.step}</div>
              </div>
            ))}
          </div>
        </div>
      </aside>
    );
  };
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between p-6 pb-2">
        <h1 className="text-2xl font-bold">Chat</h1>
        <div className="flex items-center gap-3">
          <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-sm" onClick={()=>window.aiw.getHistory()}>Load History</button>
          <div className="text-sm text-[var(--text-secondary)]">Status: {status}</div>
        </div>
      </div>
      <div className={`flex-1 flex ${hasPlan ? '': ''}`}>
        <div className="flex-1 min-w-0 px-6">
          <ErrorBanner message={lastError || null} />
          <ChatToolCalls />
          <ChatMessages />
          <div className="mt-6">
            <ChatInterface />
          </div>
        </div>
        <PlanSidebar />
      </div>
    </div>
  );
};

export default ChatWorkspace;
