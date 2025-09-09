import React, { useEffect, useRef, useState } from 'react';
import { useBackend } from '../contexts/BackendContext';
import ChatControls from './ChatControls';

const ChatInterface: React.FC = () => {
  const { status, userTurn, login, start, logs, draftMessage, setDraftMessage, chatParams, setChatParams, tokenUsage } = useBackend();
  const connected = status === 'connected';
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showCwdEditor, setShowCwdEditor] = useState(false);
  const [cwdInput, setCwdInput] = useState<string>(chatParams.cwd || '');
  const taRef = useRef<HTMLTextAreaElement | null>(null);

  // Keyboard shortcut: Ctrl/Cmd+I focuses composer
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === 'i')) {
        e.preventDefault();
        taRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const modelChipClass = (() => {
    const m = (chatParams.model || '').toLowerCase();
    if (m.startsWith('gpt')) return 'bg-violet-500/20 border-violet-500/40 text-violet-200';
    if (m.startsWith('o')) return 'bg-blue-500/20 border-blue-500/40 text-blue-200';
    if (m.includes('llama') || m.includes('mistral') || m.includes('gemma')) return 'bg-green-500/20 border-green-500/40 text-green-200';
    return 'bg-[var(--bg-tertiary)] border-[var(--border)]';
  })();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = (draftMessage || '').trim();
    if (!text) return;
    setDraftMessage('');
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
          {/* Parameter bar inside composer */}
          <div className="flex items-center flex-wrap gap-2 mb-2 text-xs sticky top-0 z-10 bg-[var(--bg-primary)]/80 backdrop-blur px-1 py-1 rounded">
          <div className={`px-2 py-1 rounded-full border ${modelChipClass} flex items-center gap-2`}>
            <span>Model:</span>
              <select
                value={chatParams.model}
                onChange={(e)=>setChatParams({ model: e.target.value })}
                className="bg-transparent border-none outline-none text-[var(--text-primary)] text-xs"
              >
                <option value="gpt-5">gpt-5</option>
                <option value="o3">o3</option>
                <option value="o4-mini">o4-mini</option>
                <option value="gpt-4o-mini">gpt-4o-mini</option>
              </select>
            </div>
            <div className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)]">Sandbox: <strong className="ml-1">{chatParams.sandbox_mode}</strong></div>
            <div className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)]">Effort: <strong className="ml-1">{chatParams.effort}</strong></div>
            <div className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)]">Approval: <strong className="ml-1">{chatParams.approval_policy}</strong></div>
            {/* Show/Hide Reasoning toggle */}
            <button
              type="button"
              onClick={() => setChatParams({ showReasoning: !chatParams.showReasoning })}
              className={`px-2 py-1 rounded-full border text-xs ${chatParams.showReasoning ? 'bg-green-500/20 border-green-500/40 text-green-300' : 'bg-[var(--bg-tertiary)] border-[var(--border)] text-[var(--text-secondary)]'}`}
              title="Toggle reasoning visibility"
            >
              Reasoning: <strong className="ml-1">{chatParams.showReasoning ? 'on' : 'off'}</strong>
            </button>

            {/* CWD chip / editor toggle */}
            {chatParams.cwd ? (
              <div className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)] flex items-center gap-2">
                <span>cwd: <strong className="ml-1">{chatParams.cwd}</strong></span>
                <button type="button" className="underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]" onClick={()=>{ setCwdInput(chatParams.cwd || ''); setShowCwdEditor(s=>!s); }}>edit</button>
                <button type="button" className="underline text-red-400 hover:text-red-300" onClick={()=> setChatParams({ cwd: undefined })}>clear</button>
              </div>
            ) : (
              <button type="button" className="px-2 py-1 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)]" onClick={()=> setShowCwdEditor(s=>!s)}>+ cwd</button>
            )}
            <button type="button" className="ml-auto px-2 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border)]" onClick={()=>setShowAdvanced(v=>!v)}>{showAdvanced ? 'Hide' : 'Edit'}</button>
          </div>
            {/* Token usage pill */}
            {tokenUsage?.context_window ? (
              <div className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)]" title={`in:${tokenUsage.input_tokens||0} out:${tokenUsage.output_tokens||0} total:${tokenUsage.total_tokens||0} / ${tokenUsage.context_window}`}>
                ctx {Math.min(100, Math.round(((tokenUsage.total_tokens||0) / (tokenUsage.context_window||1)) * 100))}%
              </div>
            ) : null}
          {showCwdEditor && (
            <div className="mb-2 p-2 border border-[var(--border)] rounded bg-[var(--bg-secondary)] flex items-center gap-2">
              <input value={cwdInput} onChange={(e)=>setCwdInput(e.target.value)} placeholder="Working directory (absolute or project path)" className="flex-1 px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-sm" />
              <button type="button" className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-sm" onClick={()=>{ setChatParams({ cwd: cwdInput || undefined }); setShowCwdEditor(false); }}>Save</button>
            </div>
          )}
          {showAdvanced && (
            <div className="mb-2 border border-[var(--border)] rounded-lg bg-[var(--bg-secondary)]">
              <ChatControls />
            </div>
          )}
          <div className="relative">
            <textarea
              ref={taRef}
              value={draftMessage}
              onChange={(e) => {
                setDraftMessage(e.target.value);
                const el = taRef.current; if (el) { el.style.height = 'auto'; const max = 6 * 24; const h = Math.min(el.scrollHeight, max); el.style.height = h + 'px'; }
              }}
              rows={2}
              placeholder={connected ? 'Delegate a task to Nexus AI...' : 'Starting backend...'}
              className="w-full bg-[var(--bg-tertiary)] rounded-lg py-3 pl-4 pr-12 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] border border-[var(--border)] resize-none leading-6"
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
        {/* dev logs removed for cleaner chat */}
      </div>
    </div>
  );
};

export default ChatInterface;
