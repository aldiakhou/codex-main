import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useBackend } from '../contexts/BackendContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import hljs from 'highlight.js';
import { IconRobot, IconUser, IconInfoCircle, IconBrain } from '@tabler/icons-react';

type Props = { showToolCalls?: boolean };
const ChatMessages: React.FC<Props> = ({ showToolCalls = true }) => {
  const { messages, chatParams, setDraftMessage, toolCalls } = useBackend();
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

  // Hide tool-role messages from inline chat; show reasoning only if enabled.
  const baseMessages = useMemo(() => messages.filter(m => m.role !== 'tool' && (m.role !== 'reasoning' || chatParams.showReasoning)), [messages, chatParams.showReasoning]);
  // Merge inline tool calls before the next assistant message.
  const filtered = useMemo(() => {
    const calls = showToolCalls ? [...(toolCalls || [])].sort((a, b) => (a.started_at||0) - (b.started_at||0)) : [];
    let ci = 0;
    const result: Array<any> = [];
    let lastTs = 0;
    for (const m of baseMessages) {
      const ts = (m as any).ts || lastTs || 0;
      // Insert tool calls that happened since the previous message timestamp, up to this message timestamp
      const inline: any[] = [];
      while (ci < calls.length) {
        const c = calls[ci];
        const t = c.ended_at || c.started_at || 0;
        if (t && t <= ts) { inline.push(c); ci++; continue; }
        break;
      }
      if (inline.length) {
        result.push({ id: `tc_${ts}_${result.length}` as any, role: 'tool-inline', calls: inline } as any);
      }
      result.push(m);
      lastTs = ts;
    }
    // trailing calls after last message
    const rest: any[] = calls.slice(ci);
    if (rest.length) result.push({ id: `tc_tail_${Date.now()}` as any, role: 'tool-inline', calls: rest } as any);
    return result;
  }, [baseMessages, toolCalls, showToolCalls]);

  // Per-call collapse/expand state
  const [tcOpen, setTcOpen] = useState<Record<string, boolean>>({});
  const toggleCall = (id: string) => setTcOpen((prev) => ({ ...prev, [id]: !prev[id] }));
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
          {m.role === 'tool-inline' ? (
            <div className="rounded-xl px-3 py-2 shadow-sm bg-blue-500/10 border border-blue-500/30">
              {(m as any).calls.map((c: any, i: number) => {
                const header = c.kind === 'exec' ? `$ ${(c.command||[]).join(' ')}` : (c.name || 'tool');
                const status = c.status === 'running' ? 'running' : `done${c.exit_code !== undefined ? ` (${c.exit_code})` : ''}`;
                const outputCombined = (c.formatted_output || c.stdout || '') + (c.stderr ? `\n[stderr]\n${c.stderr}` : '');
                const callId: string = String(c.call_id || `${(m as any).id}_${i}`);
                const isOpen = !!tcOpen[callId];
                const lines = (outputCombined || '').split(/\r?\n/);
                const previewLines = 6;
                const preview = lines.slice(0, previewLines).join('\n');
                const moreCount = Math.max(0, lines.length - previewLines);
                return (
                  <div key={callId} className="border border-[var(--border)] rounded bg-[var(--bg-secondary)] mb-2 last:mb-0">
                    <div className="w-full text-left px-3 py-2 flex items-center justify-between gap-2">
                      <div className="truncate font-mono text-sm">
                        <span className={`inline-block w-2 h-2 rounded-full mr-2 ${c.status==='running'?'bg-yellow-500 animate-pulse':'bg-green-500'}`}></span>
                        {header}
                        {c.cwd ? <span className="text-[var(--text-tertiary)] ml-2">(cwd: {c.cwd})</span> : null}
                      </div>
                      <div className="text-xs text-[var(--text-tertiary)] whitespace-nowrap flex items-center gap-2">
                        <span>{status}</span>
                        <button className="px-2 py-0.5 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs" onClick={()=>toggleCall(callId)}>
                          {isOpen ? 'Hide Output' : 'Show Output'}
                        </button>
                      </div>
                    </div>
                    {isOpen && (
                      <div className="px-3 pb-3">
                        <div className="flex gap-2 mb-2">
                          <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs" onClick={async()=>{ try { await navigator.clipboard.writeText(outputCombined); } catch {} }}>Copy Output</button>
                          <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs" onClick={()=> setDraftMessage((prev:any)=> (prev ? prev+"\n\n" : '') + '```\n' + outputCombined + '\n```')}>Quote Output</button>
                        </div>
                        <pre className="whitespace-pre-wrap text-xs font-mono bg-[var(--bg-tertiary)] border border-[var(--border)] rounded p-2 max-h-64 overflow-auto">{outputCombined || '[no output yet]'}</pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
          <div className={`rounded-xl px-3 py-2 shadow-sm ${m.role==='assistant' ? 'bg-violet-500/10' : m.role==='user' ? 'bg-green-500/10' : m.role==='system' ? 'bg-gray-500/10' : 'bg-yellow-500/10'}`}>
            <div className="flex items-center gap-2 text-2xs text-[var(--text-tertiary)]">
              {m.role === 'assistant' && <IconRobot size={14} className="text-violet-300" />}
              {m.role === 'user' && <IconUser size={14} className="text-green-300" />}
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
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          a({ href, children, ...props }) {
                            return (
                              <a href={href} target="_blank" rel="noreferrer noopener" {...props}>
                                {children}
                              </a>
                            );
                          },
                        }}
                      >
                        {m.text}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              ) : (
                <div className="prose prose-invert max-w-none text-sm">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      a({ href, children, ...props }) {
                        return (
                          <a href={href} target="_blank" rel="noreferrer noopener" {...props}>
                            {children}
                          </a>
                        );
                      },
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
          )}
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
