import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useBackend } from '../contexts/BackendContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import hljs from 'highlight.js';

const ChatMessages: React.FC = () => {
  const { messages, chatParams, setDraftMessage } = useBackend();
  const endRef = useRef<HTMLDivElement | null>(null);
  const [showScroll, setShowScroll] = useState(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  useEffect(() => {
    const target = endRef.current;
    if (!target) return;
    const io = new IntersectionObserver((entries) => {
      const e = entries[0];
      setShowScroll(!e.isIntersecting);
    }, { root: null, threshold: 0.1 });
    io.observe(target);
    return () => io.disconnect();
  }, []);

  const filtered = useMemo(() => messages.filter(m => m.role !== 'reasoning' || chatParams.showReasoning), [messages, chatParams.showReasoning]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-2 space-y-4">
      {filtered.map((m) => (
        <div key={m.id} className={`rounded-lg p-3 border ${m.role === 'reasoning' ? 'bg-yellow-500/10 border-yellow-500/30' : m.role === 'tool' ? 'bg-blue-500/10 border-blue-500/30' : m.role === 'system' ? 'bg-gray-500/10 border-gray-500/30' : 'bg-[var(--bg-secondary)] border-[var(--border)]'}`}>
          <div className="text-xs text-[var(--text-tertiary)] mb-1 uppercase tracking-wide flex items-center gap-2 justify-between">
            <span className={`inline-block w-2 h-2 rounded-full ${m.role === 'assistant' ? 'bg-violet-400' : m.role === 'reasoning' ? 'bg-yellow-400' : m.role === 'tool' ? 'bg-blue-400' : m.role === 'user' ? 'bg-green-400' : 'bg-gray-400'}`} />
            <span className="mr-auto ml-2">{m.role}</span>
            <span className="text-2xs mr-2">{(m as any).ts ? new Date((m as any).ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
            <div className="flex gap-2">
              <button className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-2xs" onClick={async ()=>{ try { await navigator.clipboard.writeText(m.text); } catch {} }}>Copy</button>
              <button className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-2xs" onClick={()=> setDraftMessage(prev => (prev ? prev+"\n\n" : '') + '> ' + m.text.replace(/\n/g,'\n> ') )}>Reply</button>
            </div>
          </div>
          <div className="prose prose-invert max-w-none text-[var(--text-primary)]">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({node, inline, className, children, ...props}) {
                  const txt = String(children || '');
                  const langMatch = /language-(\w+)/.exec(className || '');
                  if (inline) {
                    return <code className={className} {...props}>{children}</code>;
                  }
                  let html = '';
                  try {
                    if (langMatch) html = hljs.highlight(txt, { language: langMatch[1] }).value;
                    else html = hljs.highlightAuto(txt).value;
                  } catch (e) { html = txt; }
                  return <pre className="hljs"><code dangerouslySetInnerHTML={{ __html: html }} /></pre>;
                }
              }}
            >
              {m.text}
            </ReactMarkdown>
          </div>
        </div>
      ))}
      <div ref={endRef} />
      {showScroll && (
        <button onClick={()=> endRef.current?.scrollIntoView({ behavior: 'smooth' })} className="fixed bottom-28 right-8 px-3 py-2 rounded-full bg-[var(--accent)] text-white shadow-lg">
          Scroll to latest
        </button>
      )}
    </div>
  );
};

export default ChatMessages;
