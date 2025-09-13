import React, { useEffect, useRef, useState } from 'react';
import { useBackend } from '../contexts/BackendContext';
import ChatControls from './ChatControls';

async function fileToDataUrl(file: Blob): Promise<string> {
  return new Promise((resolve) => {
    try {
      const fr = new FileReader();
      fr.onload = () => resolve(typeof fr.result === 'string' ? fr.result : '');
      fr.onerror = () => resolve('');
      fr.readAsDataURL(file);
    } catch {
      resolve('');
    }
  });
}

const ChatInterface: React.FC = () => {
  const { status, userTurn, login, start, interrupt, logs, draftMessage, setDraftMessage, chatParams, setChatParams, tokenUsage, customPrompts, refreshCustomPrompts } = useBackend();
  const connected = status === 'connected';
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showCwdEditor, setShowCwdEditor] = useState(false);
  const [cwdInput, setCwdInput] = useState<string>(chatParams.cwd || '');
  const [promptSelect, setPromptSelect] = useState<string>('');
  const [attachedImages, setAttachedImages] = useState<string[]>([]); // local file paths
  const [attachedImageUrls, setAttachedImageUrls] = useState<string[]>([]); // data: URLs (from paste)
  const [previews, setPreviews] = useState<Record<string, string>>({}); // path -> data URL
  // @-file search overlay state
  const [fsOpen, setFsOpen] = useState<boolean>(false);
  const [fsQuery, setFsQuery] = useState<string>('');
  const [fsSel, setFsSel] = useState<number>(0);
  const [fsResults, setFsResults] = useState<Array<{ path: string; rel?: string }>>([]);

  // Load previews for local image paths
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      const out: Record<string, string> = {};
      for (const p of attachedImages) {
        if (!p) continue;
        try {
          // @ts-ignore
          const res = await window.fsapi.readBase64(p);
          if (res && res.ok && res.base64 && !cancelled) {
            const lower = p.toLowerCase();
            const type = lower.endsWith('.png') ? 'image/png' : lower.endsWith('.gif') ? 'image/gif' : lower.endsWith('.webp') ? 'image/webp' : 'image/jpeg';
            out[p] = `data:${type};base64,${res.base64}`;
          }
        } catch {}
      }
      if (!cancelled) setPreviews(out);
    })();
    return () => { cancelled = true; };
  }, [attachedImages.join('|')]);
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
    if (!text && attachedImages.length === 0) return;
    setDraftMessage('');
    let imgs = attachedImages.slice(0);
    let urls = attachedImageUrls.slice(0);
    // Optional downscale before sending
    try {
      const down = localStorage.getItem('vision.downscale') === 'true';
      const maxDim = Math.max(64, parseInt(localStorage.getItem('vision.maxDim') || '1280', 10) || 1280);
      if (down) {
        // Downscale local paths into data URLs
        const converted: string[] = [];
        for (const p of imgs) {
          try {
            // @ts-ignore
            const res = await window.fsapi.readBase64(p);
            if (res && res.ok && res.base64) {
              const lower = p.toLowerCase();
              const type = lower.endsWith('.png') ? 'image/png' : lower.endsWith('.gif') ? 'image/gif' : lower.endsWith('.webp') ? 'image/webp' : 'image/jpeg';
              const dataUrl = `data:${type};base64,${res.base64}`;
              const scaled = await downscaleDataUrl(dataUrl, maxDim);
              converted.push(scaled || dataUrl);
            } else {
              // fallback to local path if read fails
              converted.push('');
            }
          } catch {
            converted.push('');
          }
        }
        // Replace successful conversions; drop blanks
        urls = [...converted.filter(Boolean), ...urls];
        imgs = [];
        // Downscale pasted URLs too
        const scaledUrls: string[] = [];
        for (const u of urls) {
          try {
            const scaled = await downscaleDataUrl(u, maxDim);
            scaledUrls.push(scaled || u);
          } catch { scaledUrls.push(u); }
        }
        urls = scaledUrls;
      }
    } catch {}

    setAttachedImages([]);
    setAttachedImageUrls([]);
    await userTurn(text, { local_images: imgs, image_urls: urls });
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
            {status !== 'connected' ? (
              <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={() => start()}>Start</button>
            ) : (
              <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={() => interrupt()}>Interrupt</button>
            )}
            {/* Login moved to Settings */}
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
            {/* Attach Images */}
            <button
              type="button"
              className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs"
              onClick={async()=>{
                try {
                  const res = await window.fsapi.chooseFiles(true);
                  if (res && res.ok && Array.isArray(res.paths)) {
                    setAttachedImages((prev)=> Array.from(new Set([...(prev||[]), ...res.paths!])));
                  }
                } catch {}
              }}
            >Attach image</button>
            {/* Custom prompts picker */}
            <div className="px-2 py-1 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border)] flex items-center gap-2">
              <span>Prompt:</span>
              <select
                value={promptSelect}
                onFocus={()=>{ try { refreshCustomPrompts(); } catch {} }}
                onChange={(e)=>{
                  const id = e.target.value;
                  setPromptSelect('');
                  const p = (customPrompts||[]).find((x)=> x.name === id);
                  if (p && p.content) setDraftMessage((prev)=> (prev ? prev+"\n\n" : '') + p.content);
                }}
                className="bg-transparent border-none outline-none text-[var(--text-primary)] text-xs"
              >
                <option value="">Insert…</option>
                {(customPrompts||[]).map((p)=> (
                  <option key={p.name} value={p.name}>{p.name}</option>
                ))}
              </select>
            </div>
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
          <div className="relative" onDragOver={(e)=>{ e.preventDefault(); e.dataTransfer.dropEffect='copy'; }} onDrop={(e)=>{ e.preventDefault(); try { const files = Array.from(e.dataTransfer.files||[]); const imgs = files.filter(f=>/^image\//.test(f.type)); const paths = imgs.map((f:any)=> f.path).filter(Boolean); if (paths.length) setAttachedImages(prev=> Array.from(new Set([...(prev||[]), ...paths]))); } catch {} }}>
            {(attachedImages.length || attachedImageUrls.length) ? (
              <div className="mb-2 flex flex-wrap gap-2">
                {attachedImages.map((p) => (
                  <div key={p} className="flex items-center gap-2 text-2xs px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
                    <div className="w-14 h-14 bg-black/20 rounded overflow-hidden flex items-center justify-center">
                      {previews[p] ? <img src={previews[p]} alt={p} className="w-full h-full object-contain" /> : <span className="text-[var(--text-tertiary)]">img</span>}
                    </div>
                    <div className="flex flex-col">
                      <span className="font-mono truncate max-w-[14rem]" title={p}>{p.replace(/.*[\\/]/,'')}</span>
                      <div className="flex gap-2">
                        <button type="button" className="underline text-[var(--text-tertiary)]" onClick={()=> setAttachedImages((prev)=> prev.filter(x=>x!==p))}>Remove</button>
                        <button type="button" className="underline text-[var(--text-tertiary)]" onClick={async()=>{ try { await (window as any).fsapi.openPath(p); } catch {} }}>Open</button>
                      </div>
                    </div>
                  </div>
                ))}
                {attachedImageUrls.map((u, idx) => (
                  <div key={`url_${idx}`} className="flex items-center gap-2 text-2xs px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]">
                    <div className="w-14 h-14 bg-black/20 rounded overflow-hidden flex items-center justify-center">
                      <img src={u} alt={`img_${idx}`} className="w-full h-full object-contain" />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-mono truncate max-w-[14rem]" title={u.slice(0,64)}>(pasted image)</span>
                      <div className="flex gap-2">
                        <button type="button" className="underline text-[var(--text-tertiary)]" onClick={()=> setAttachedImageUrls((prev)=> prev.filter((_,i)=>i!==idx))}>Remove</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
            <textarea
              ref={taRef}
              value={draftMessage}
              onChange={(e) => {
                setDraftMessage(e.target.value);
                const el = taRef.current; if (el) { el.style.height = 'auto'; const max = 6 * 24; const h = Math.min(el.scrollHeight, max); el.style.height = h + 'px'; }
                // update @-file search state
                try {
                  const caret = (e.target as HTMLTextAreaElement).selectionStart || 0;
                  const before = e.target.value.slice(0, caret);
                  const m = /(^|\s)@([^\s]*)$/.exec(before);
                  if (m) {
                    const q = m[2] || '';
                    setFsOpen(true);
                    setFsQuery(q);
                    (async () => {
                      const res = await window.idx.search(q, 20, chatParams.cwd || undefined);
                      setFsResults((res && res.ok ? res.matches : []) as any);
                      setFsSel(0);
                    })().catch(()=>{});
                  } else {
                    setFsOpen(false);
                    setFsQuery('');
                    setFsResults([]);
                  }
                } catch {}
              }}
              onKeyDown={(e)=>{
                if (!fsOpen) return;
                if (['ArrowDown','ArrowUp','Tab','Enter','Escape'].includes(e.key)) {
                  e.stopPropagation();
                }
                if (e.key === 'ArrowDown') {
                  e.preventDefault();
                  setFsSel((i)=> Math.min(i + 1, Math.max(0, fsResults.length - 1)));
                } else if (e.key === 'ArrowUp') {
                  e.preventDefault();
                  setFsSel((i)=> Math.max(i - 1, 0));
                } else if (e.key === 'Escape') {
                  e.preventDefault(); setFsOpen(false);
                } else if (e.key === 'Enter' || e.key === 'Tab') {
                  e.preventDefault();
                  const pick = fsResults[fsSel];
                  if (pick) {
                    const ta = taRef.current;
                    const text = draftMessage;
                    if (ta) {
                      const caret = ta.selectionStart || 0;
                      const before = text.slice(0, caret);
                      const after = text.slice(caret);
                      const m = /(^|\s)@([^\s]*)$/.exec(before);
                      if (m) {
                        const prefix = before.slice(0, before.length - (m[2] ? m[2].length : 0) - 1); // drop '@query'
                        const insert = (pick.rel || pick.path);
                        const next = prefix + insert + after;
                        setDraftMessage(next);
                        setTimeout(()=>{
                          try { if (taRef.current) { const pos = prefix.length + insert.length; taRef.current.selectionStart = pos; taRef.current.selectionEnd = pos; } } catch {}
                        }, 0);
                      }
                    }
                    setFsOpen(false);
                  }
                }
              }}
              onPaste={async(e)=>{
                try {
                  const files = Array.from(e.clipboardData?.files || []);
                  const imgs = files.filter(f => f && f.type && f.type.startsWith('image/'));
                  if (imgs.length) {
                    e.preventDefault();
                    const paths: string[] = [];
                    const urls: string[] = [];
                    for (const f of imgs) {
                      const anyFile: any = f as any;
                      if (anyFile.path) {
                        paths.push(anyFile.path as string);
                      } else {
                        const dataUrl = await fileToDataUrl(f);
                        if (dataUrl) urls.push(dataUrl);
                      }
                    }
                    if (paths.length) setAttachedImages(prev => Array.from(new Set([...(prev||[]), ...paths])));
                    if (urls.length) setAttachedImageUrls(prev => [...(prev||[]), ...urls]);
                  } else {
                    // Fallback to Async Clipboard API
                    try {
                      // @ts-ignore
                      if (navigator.clipboard && navigator.clipboard.read) {
                        // @ts-ignore
                        const items = await navigator.clipboard.read();
                        const urls: string[] = [];
                        for (const item of items) {
                          for (const type of item.types || []) {
                            if (type.startsWith('image/')) {
                              const blob = await item.getType(type);
                              const dataUrl = await fileToDataUrl(blob);
                              if (dataUrl) urls.push(dataUrl);
                            }
                          }
                        }
                        if (urls.length) {
                          e.preventDefault();
                          setAttachedImageUrls(prev => [...(prev||[]), ...urls]);
                        }
                      }
                    } catch {}
                  }
                } catch {}
              }}
              rows={2}
              placeholder={connected ? 'Delegate a task to Nexus AI...' : 'Starting backend...'}
              className="w-full bg-[var(--bg-tertiary)] rounded-lg py-3 pl-4 pr-12 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] border border-[var(--border)] resize-none leading-6"
              disabled={false}
            />
            {fsOpen && fsResults.length > 0 && (
              <div className="absolute left-2 right-10 -bottom-1 translate-y-full z-20 max-h-64 overflow-auto border border-[var(--border)] rounded-md bg-[var(--bg-secondary)] shadow-lg">
                {fsResults.map((r, idx) => (
                  <div key={r.path + ':' + idx} className={`flex items-center gap-2 px-2 py-1 ${idx===fsSel ? 'bg-[var(--bg-tertiary)]' : ''}`} onMouseEnter={()=> setFsSel(idx)}>
                    <button
                      type="button"
                      className="flex-1 text-left text-xs font-mono truncate"
                      title={r.path}
                      onMouseDown={(ev)=>{ ev.preventDefault(); }}
                      onClick={()=>{
                        const ta = taRef.current;
                        const text = draftMessage;
                        if (!ta) return;
                        const caret = ta.selectionStart || 0;
                        const before = text.slice(0, caret);
                        const after = text.slice(caret);
                        const m = /(^|\s)@([^\s]*)$/.exec(before);
                        if (!m) { setFsOpen(false); return; }
                        const prefix = before.slice(0, before.length - (m[2] ? m[2].length : 0) - 1);
                        const insert = (r.rel || r.path);
                        const next = prefix + insert + after;
                        setDraftMessage(next);
                        setTimeout(()=>{ try { if (taRef.current) { const pos = prefix.length + insert.length; taRef.current.selectionStart = pos; taRef.current.selectionEnd = pos; } } catch {} }, 0);
                        setFsOpen(false);
                      }}
                    >
                      {r.rel || r.path}
                    </button>
                    <button
                      type="button"
                      className="text-2xs underline text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
                      onMouseDown={(ev)=>{ ev.preventDefault(); }}
                      onClick={async()=>{ try { await (window as any).fsapi.openPath(r.path); } catch {} }}
                    >Open</button>
                  </div>
                ))}
              </div>
            )}
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

async function downscaleDataUrl(dataUrl: string, maxDim: number): Promise<string> {
  return new Promise((resolve) => {
    try {
      const img = new Image();
      img.onload = () => {
        try {
          let { width, height } = img;
          if (width <= maxDim && height <= maxDim) {
            resolve(dataUrl);
            return;
          }
          const scale = Math.min(maxDim / width, maxDim / height);
          const w = Math.max(1, Math.round(width * scale));
          const h = Math.max(1, Math.round(height * scale));
          const canvas = document.createElement('canvas');
          canvas.width = w; canvas.height = h;
          const ctx = canvas.getContext('2d');
          if (!ctx) { resolve(dataUrl); return; }
          ctx.drawImage(img, 0, 0, w, h);
          // Preserve type if possible
          const typeMatch = /^data:(image\/[a-zA-Z0-9.+-]+);/i.exec(dataUrl);
          const mime = typeMatch ? typeMatch[1] : 'image/png';
          const out = canvas.toDataURL(mime, 0.92);
          resolve(out);
        } catch { resolve(dataUrl); }
      };
      img.onerror = () => resolve(dataUrl);
      img.src = dataUrl;
    } catch { resolve(dataUrl); }
  });
}
