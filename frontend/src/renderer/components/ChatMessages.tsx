import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useBackend } from '../contexts/BackendContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import hljs from 'highlight.js';
import { IconRobot, IconUser, IconInfoCircle, IconBrain } from '@tabler/icons-react';

type Props = { showToolCalls?: boolean; scrollRootRef?: React.RefObject<HTMLDivElement> };
const ChatMessages: React.FC<Props> = ({ showToolCalls = true, scrollRootRef }) => {
  const { messages, chatParams, setDraftMessage, toolCalls, plan, turnDiff } = useBackend();
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
    const rootEl = scrollRootRef?.current || null;
    const io = new IntersectionObserver((entries) => {
      const e = entries[0];
      setShowScroll(!e.isIntersecting);
    }, { root: rootEl, threshold: 0.1 });
    io.observe(target);
    return () => io.disconnect();
  }, [scrollRootRef?.current]);

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

  // Diff panel state (auto-open when new diff arrives)
  const [showDiff, setShowDiff] = useState<boolean>(false);
  const [sideBySide, setSideBySide] = useState<boolean>(false);
  const prevDiffRef = useRef<string | null>(null);
  useEffect(() => {
    if (turnDiff && turnDiff !== prevDiffRef.current) {
      setShowDiff(true);
      prevDiffRef.current = turnDiff;
    }
  }, [turnDiff]);

  // Build a simple side-by-side alignment from unified diff lines.
  // Strategy: group consecutive '-' and '+' blocks and zip them; context lines
  // (' ' or others) flush any pending blocks and render as identical pairs.
  const sbsRows = useMemo(() => {
    if (!turnDiff) return [] as Array<{ left: string; right: string; kind: 'ctx' | 'del' | 'add' }>;
    const rows: Array<{ left: string; right: string; kind: 'ctx' | 'del' | 'add' }> = [];
    const lines = (turnDiff || '').split(/\r?\n/);
    let dels: string[] = [];
    let adds: string[] = [];
    const flushBlocks = () => {
      const n = Math.max(dels.length, adds.length);
      for (let i = 0; i < n; i++) {
        const l = dels[i];
        const r = adds[i];
        if (l !== undefined && r !== undefined) {
          // paired change; style both sides
          rows.push({ left: l, right: r, kind: 'del' });
        } else if (l !== undefined) {
          rows.push({ left: l, right: '', kind: 'del' });
        } else if (r !== undefined) {
          rows.push({ left: '', right: r, kind: 'add' });
        }
      }
      dels = []; adds = [];
    };
    for (const raw of lines) {
      const l = raw;
      if (l.startsWith('---') || l.startsWith('+++') || l.startsWith('@@')) {
        // hunk/file headers: flush blocks and render as context headers mirrored
        flushBlocks();
        rows.push({ left: l, right: l, kind: 'ctx' });
        continue;
      }
      if (l.startsWith('-')) { dels.push(l); continue; }
      if (l.startsWith('+')) { adds.push(l); continue; }
      // context line: flush any pending +/- blocks, then mirror
      flushBlocks();
      rows.push({ left: l, right: l, kind: 'ctx' });
    }
    flushBlocks();
    return rows;
  }, [turnDiff]);

  // Extract image paths mentioned in messages and try to preview
  const imagePaths = useMemo(() => {
    const set = new Set<string>();
    const exts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'];
    const pathRegex = /(?:[A-Za-z]:\\[^\s\"']+|\/(?:[^\s\"']+\/)*[^\s\"']+)/g; // basic Win/Unix path matcher
    for (const m of messages) {
      const text = (m as any).text || '';
      if (!text || typeof text !== 'string') continue;
      const matches = text.match(pathRegex);
      if (matches) {
        for (let p of matches) {
          const lower = p.toLowerCase();
          if (exts.some(ext => lower.endsWith(ext))) set.add(p);
        }
      }
    }
    return Array.from(set).slice(-6); // show up to 6 recent
  }, [messages]);

  const [imageData, setImageData] = useState<Record<string, string>>({});
  const [toast, setToast] = useState<{ text: string; ts: number } | null>(null);
  const showToast = (text: string, ms: number = 2500) => {
    const ts = Date.now();
    setToast({ text, ts });
    window.setTimeout(() => {
      setToast((cur) => (cur && cur.ts === ts ? null : cur));
    }, ms);
  };
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const out: Record<string, string> = {};
      for (const p of imagePaths) {
        try {
          // electron preload bridge: read as base64
          // @ts-ignore
          const res = await window.fsapi.readBase64(p);
          if (res && res.ok && res.base64 && !cancelled) {
            // naive type guess by extension
            const lower = p.toLowerCase();
            const type = lower.endsWith('.png') ? 'image/png' : lower.endsWith('.gif') ? 'image/gif' : lower.endsWith('.webp') ? 'image/webp' : 'image/jpeg';
            out[p] = `data:${type};base64,${res.base64}`;
          }
        } catch {}
      }
      if (!cancelled) setImageData(out);
    })();
    return () => { cancelled = true; };
  }, [imagePaths.join('|')]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-2 space-y-4">
      {/* Compact Plan bar */}
      {plan && plan.plan && plan.plan.length ? (
        <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-tertiary)] p-2">
          <div className="text-2xs text-[var(--text-tertiary)] mb-1">Plan</div>
          <div className="flex flex-wrap gap-3 items-center text-xs">
            {plan.plan.map((it, idx) => (
              <div key={idx} className="flex items-center gap-1">
                <span className={`w-2 h-2 rounded-full ${it.status === 'completed' ? 'bg-green-400' : it.status === 'in_progress' ? 'bg-blue-400 animate-pulse' : 'bg-zinc-500'}`} />
                <span className="font-medium">{it.step}</span>
              </div>
            ))}
          </div>
          {plan.explanation ? (
            <div className="mt-1 text-2xs text-[var(--text-secondary)] break-words">{plan.explanation}</div>
          ) : null}
        </div>
      ) : null}
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
                            const h = String(href || '');
                            const isLocal = /^(?:[A-Za-z]:\\|\/)/.test(h);
                            return (
                              <a
                                href={h}
                                target={isLocal ? undefined : '_blank'}
                                rel={isLocal ? undefined : 'noreferrer noopener'}
                                onClick={(e)=>{ if (isLocal) { e.preventDefault(); try { /* @ts-ignore */ window.fsapi.openPath(h); } catch {} } }}
                                {...props}
                              >
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
                        const h = String(href || '');
                        const isLocal = /^(?:[A-Za-z]:\\|\/)/.test(h);
                        return (
                          <a
                            href={h}
                            target={isLocal ? undefined : '_blank'}
                            rel={isLocal ? undefined : 'noreferrer noopener'}
                            onClick={(e)=>{ if (isLocal) { e.preventDefault(); try { /* @ts-ignore */ window.fsapi.openPath(h); } catch {} } }}
                            {...props}
                          >
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
                        // Do not return <pre> here; ReactMarkdown wraps block code in <pre>.
                        return <code className={`hljs ${className||''}`} dangerouslySetInnerHTML={{ __html: html }} {...props} />;
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
              {m.role === 'user' ? (
                <button className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-2xs" onClick={()=> setDraftMessage(String((m as any).text || ''))}>Edit</button>
              ) : (
                <button className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-2xs" onClick={()=> setDraftMessage(prev => (prev ? prev+"\n\n" : '') + '> ' + String((m as any).text || '').replace(/\n/g,'\n> ') )}>Reply</button>
              )}
            </div>
          </div>
          )}
        </div>
      ))}
      <div ref={endRef} />
      {/* Unified diff panel */}
      {turnDiff ? (
        <div className="mt-4 rounded-lg border border-[var(--border)] bg-[var(--bg-tertiary)] p-2">
          <div className="flex items-center justify-between">
            <div className="text-xs font-semibold">Latest Changes (unified diff)</div>
            <div className="flex items-center gap-2">
              <button className="text-2xs underline text-[var(--text-tertiary)]" onClick={()=>setShowDiff(s=>!s)}>{showDiff ? 'Hide' : 'Show'}</button>
              {showDiff && (
                <button className={`text-2xs underline ${sideBySide ? 'text-[var(--text-primary)]' : 'text-[var(--text-tertiary)]'}`} onClick={()=>setSideBySide(s=>!s)}>{sideBySide ? 'Inline' : 'Side-by-side'}</button>
              )}
              <button className="text-2xs underline text-[var(--text-tertiary)]" onClick={()=>{ try { navigator.clipboard?.writeText(turnDiff); } catch {} }}>Copy</button>
            </div>
          </div>
          {showDiff && (!sideBySide ? (
            <pre className="mt-2 text-xs overflow-auto max-h-80 p-2 rounded bg-black/20 border border-[var(--border)]">
              <code className="hljs language-diff" dangerouslySetInnerHTML={{ __html: (()=>{ try { return hljs.highlight(turnDiff, { language: 'diff' }).value; } catch { return turnDiff.replace(/[&<>]/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;'} as any)[s]); }})() }} />
            </pre>
          ) : (
            <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2">
              <pre className="text-xs overflow-auto max-h-80 p-2 rounded bg-black/20 border border-[var(--border)]">
                <code className="hljs">
                  {sbsRows.map((r, i) => {
                    const isHeader = (r.left || '').startsWith('@@') || (r.left || '').startsWith('---') || (r.left || '').startsWith('+++');
                    const cls = isHeader ? 'bg-indigo-900/30' : (r.kind==='del' ? 'bg-red-900/20' : r.kind==='add' ? 'bg-green-900/10' : '');
                    return (
                      <div key={`l${i}`} className={cls}>{String(r.left || '').replace(/[&<>]/g, (s) => ({'&':'&amp;','<':'&lt;','>':'&gt;'} as any)[s])}</div>
                    );
                  })}
                </code>
              </pre>
              <pre className="text-xs overflow-auto max-h-80 p-2 rounded bg-black/20 border border-[var(--border)]">
                <code className="hljs">
                  {sbsRows.map((r, i) => {
                    const isHeader = (r.right || '').startsWith('@@') || (r.right || '').startsWith('---') || (r.right || '').startsWith('+++');
                    const cls = isHeader ? 'bg-indigo-900/30' : (r.kind==='add' ? 'bg-green-900/20' : r.kind==='del' ? 'bg-red-900/10' : '');
                    return (
                      <div key={`r${i}`} className={cls}>{String(r.right || '').replace(/[&<>]/g, (s) => ({'&':'&amp;','<':'&lt;','>':'&gt;'} as any)[s])}</div>
                    );
                  })}
                </code>
              </pre>
            </div>
          ))}
        </div>
      ) : null}

      {/* Attached Images (best-effort) */}
      {imagePaths.length ? (
        <div className="mt-4 rounded-lg border border-[var(--border)] bg-[var(--bg-tertiary)] p-2">
          <div className="text-xs font-semibold mb-2">Attached Images (detected)</div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {imagePaths.map((p) => (
              <div key={p} className="border border-[var(--border)] rounded p-2 bg-black/20">
                {imageData[p] ? (
                  <img src={imageData[p]} alt={p} className="w-full h-32 object-contain bg-black/40 rounded" />
                ) : (
                  <div className="w-full h-32 bg-black/20 rounded flex items-center justify-center text-2xs text-[var(--text-tertiary)]">(unavailable)</div>
                )}
                <div className="mt-1 text-2xs truncate text-[var(--text-tertiary)]" title={p}>{p}</div>
                <div className="mt-1 flex gap-2 justify-end">
                  <button className="text-2xs underline text-[var(--text-tertiary)]" onClick={()=>{ try { navigator.clipboard.writeText(p); showToast('Path copied'); } catch { showToast('Copy failed'); } }}>Copy path</button>
                  <button className="text-2xs underline text-[var(--text-tertiary)]" onClick={async ()=>{
                    try {
                      // @ts-ignore
                      const res = await window.fsapi.openPath(p);
                      if (!res || !res.ok) showToast('Failed to open path');
                      else showToast('Opening…');
                    } catch {
                      showToast('Failed to open path');
                    }
                  }}>Open</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 px-3 py-2 rounded bg-black/80 border border-white/10 text-2xs text-white shadow-lg">
          {toast.text}
        </div>
      )}
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
