import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useBackend } from '../contexts/BackendContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import hljs from 'highlight.js';
import { IconRobot, IconUser, IconTools, IconInfoCircle, IconBrain } from '@tabler/icons-react';

const ChatMessages: React.FC = () => {
  const { messages, chatParams, setDraftMessage } = useBackend();
  const endRef = useRef<HTMLDivElement | null>(null);
  const nodeRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const [showScroll, setShowScroll] = useState(false);
  const [firstUnreadId, setFirstUnreadId] = useState<string | null>(null);

  useEffect(() => {
    if (!showScroll) {
      endRef.current?.scrollIntoView({ behavior: 'smooth' });
    } else {
      // New message while scrolled up: mark first unread
      const last = messages[messages.length - 1] as any;
      if (last && !firstUnreadId) setFirstUnreadId(last.id as string);
    }
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
  const [collapse, setCollapse] = useState<Record<string, boolean>>({});
  const toggle = (id: string) => setCollapse((prev) => ({ ...prev, [id]: !prev[id] }));

  return (
    <div className="max-w-4xl mx-auto px-4 py-2 space-y-4">
      {filtered.map((m) => (
        <div key={m.id} ref={(el)=>{ nodeRefs.current[String((m as any).id)] = el }} className="space-y-1">
          {/* turn separator with date before user messages (except first) */}
          {m.role === 'user' ? (
            <div className="flex items-center gap-2 my-2">
              <div className="flex-1 h-px bg-white/10"></div>
              <div className="text-2xs text-[var(--text-tertiary)]">{(m as any).ts ? new Date((m as any).ts).toLocaleString([], { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''}</div>
              <div className="flex-1 h-px bg-white/10"></div>
            </div>
          ) : null}
          <div className={`rounded-xl px-3 py-2 shadow-sm ${m.role==='assistant' ? 'bg-violet-500/10' : m.role==='user' ? 'bg-green-500/10' : m.role==='tool' ? 'bg-blue-500/10' : m.role==='system' ? 'bg-gray-500/10' : 'bg-yellow-500/10'}`}>
            <div className="flex items-center gap-2 text-2xs text-[var(--text-tertiary)]">
              {m.role === 'assistant' && <IconRobot size={14} className="text-violet-300" />}
              {m.role === 'user' && <IconUser size={14} className="text-green-300" />}
              {m.role === 'tool' && <IconTools size={14} className="text-blue-300" />}
              {m.role === 'reasoning' && <IconBrain size={14} className="text-yellow-300" />}
              {m.role === 'system' && <IconInfoCircle size={14} className="text-gray-300" />}
              <span className="uppercase">{m.role}</span>
              <span className="ml-auto">{(m as any).ts ? new Date((m as any).ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
            </div>
            <div className="mt-1 text-[var(--text-primary)]">
              {m.role === 'reasoning' ? (
                <div>
                  <button className="text-2xs underline text-[var(--text-tertiary)]" onClick={()=>toggle(m.id as string)}>{collapse[m.id as string] ? 'Hide thoughts' : 'Show thoughts'}</button>
                  {collapse[m.id as string] && (
                    <div className="mt-1 text-sm">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                    </div>
                  )}
                </div>
              ) : (
                <div className="prose prose-invert max-w-none text-sm">
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
              )}
            </div>
            <div className="flex gap-2 mt-2 justify-end">
              <button className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-2xs" onClick={async ()=>{ try { await navigator.clipboard.writeText(m.text); } catch {} }}>Copy</button>
              <button className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-2xs" onClick={()=> setDraftMessage(prev => (prev ? prev+"\n\n" : '') + '> ' + m.text.replace(/\n/g,'\n> ') )}>Reply</button>
            </div>
          </div>
        </div>
      ))}
      <div ref={endRef} />
      {(showScroll || firstUnreadId) && (
        <button onClick={()=> endRef.current?.scrollIntoView({ behavior: 'smooth' })} className="fixed bottom-28 right-8 px-3 py-2 rounded-full bg-[var(--accent)] text-white shadow-lg">
          Scroll to latest
        </button>
      )}
      {firstUnreadId && (
        <button onClick={()=> { const el = nodeRefs.current[firstUnreadId!]; if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); setFirstUnreadId(null); }} className="fixed bottom-40 right-8 px-3 py-2 rounded-full bg-blue-600 text-white shadow-lg">
          Jump to new
        </button>
      )}
    </div>
  );
};

export default ChatMessages;
