import React, { useEffect, useMemo, useState } from 'react';
import { useBackend } from '../../contexts/BackendContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import hljs from 'highlight.js';
import DOMPurify from 'dompurify';
import { marked } from 'marked';
import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import mammoth from 'mammoth';

// lightweight helpers to avoid adding path-browserify
const pathExt = (p: string) => {
  const i = p.lastIndexOf('.');
  const j = Math.max(p.lastIndexOf('/'), p.lastIndexOf('\\'));
  return i > j ? p.slice(i) : '';
};
const pathDir = (p: string) => {
  const i = Math.max(p.lastIndexOf('/'), p.lastIndexOf('\\'));
  return i > 1 ? p.slice(0, i) : p;
};

const isTextExt = (ext: string) =>
  [
    '.md',
    '.txt',
    '.json',
    '.js',
    '.ts',
    '.tsx',
    '.jsx',
    '.css',
    '.html',
    '.xml',
    '.yaml',
    '.yml',
    '.csv',
    '.rs',
    '.py',
    '.java',
    '.go',
    '.rb',
    '.sh',
    '.ps1',
    '.toml',
  ].includes(ext);

const FilesWorkspace: React.FC = () => {
  const { chatParams, setChatParams } = useBackend();
  const [cwd, setCwd] = useState<string>(chatParams.cwd || '');
  const [entries, setEntries] = useState<Array<{ name: string; path: string; isDir: boolean }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState<string>('');
  const [backlinks, setBacklinks] = useState<Array<{ from: string; anchor?: string }>>([]);
  const [indexStatus, setIndexStatus] = useState<string>('');
  const [watching, setWatching] = useState<boolean>(false);
  const [renameDraft, setRenameDraft] = useState<string>('');
  const [downloadUrl, setDownloadUrl] = useState<string>('');
  const [downloadName, setDownloadName] = useState<string>('');

  const loadDir = async (dir: string) => {
    setError(null);
    const res = await window.fsapi.list(dir);
    if (!res.ok) {
      setError(res.error || 'Failed to list');
      setEntries([]);
      return;
    }
    setEntries(res.entries || []);
  };
  useEffect(() => {
    if (cwd) loadDir(cwd);
  }, [cwd]);

  // Listen for graph-driven file open requests
  useEffect(() => {
    const handler = () => {
      try {
        const p = localStorage.getItem('files:openPath');
        if (p) {
          const dir = pathDir(p);
          if (!cwd) setCwd(dir);
          open(p);
        }
      } catch {}
    };
    window.addEventListener('open-file-in-files', handler);
    return () => window.removeEventListener('open-file-in-files', handler);
  }, [cwd]);

  useEffect(() => {
    const off = window.idx.onUpdate(async ({ stats }) => {
      setIndexStatus(`Indexed ${stats.files} files / ${stats.links} links (watch)`);
      if (selected) {
        const b = await window.idx.backlinks(selected);
        setBacklinks(b.ok ? (b.backlinks || []) : []);
      }
    });
    return () => {
      try {
        off();
      } catch {}
    };
  }, [selected, cwd]);

  const chooseDir = async () => {
    const res = await window.fsapi.chooseDir();
    if (res.ok && res.path) setCwd(res.path);
  };
  const useInChat = () => {
    if (cwd) setChatParams({ cwd });
  };

  const open = async (p: string) => {
    setSelected(p);
    const st = await window.fsapi.stat(p);
    if (!st.ok) {
      setError(st.error || 'stat failed');
      return;
    }
    if (st.stat?.isDir) {
      setCwd(p);
      return;
    }
    const ext = pathExt(p).toLowerCase();
    setDownloadUrl('');
    setDownloadName('');
    // Rich previews by type
    if (ext === '.pdf') {
      const rr = await window.fsapi.readBase64(p);
      const base64 = rr.ok ? rr.base64 || '' : '';
      setContent(base64 ? `data:application/pdf;base64,${base64}` : '[failed to load pdf]');
    } else if (ext === '.docx') {
      const rr = await window.fsapi.readBase64(p);
      if (rr.ok && rr.base64) {
        const bin = atob(rr.base64);
        const buf = new ArrayBuffer(bin.length);
        const view = new Uint8Array(buf);
        for (let i = 0; i < bin.length; i++) view[i] = bin.charCodeAt(i);
        try {
          const result = await mammoth.convertToHtml({ arrayBuffer: buf });
          const html = DOMPurify.sanitize(result.value || '');
          setContent(`__HTML_IFRAME__${html}`);
        } catch {
          setContent('[failed to render docx]');
        }
      } else setContent('[failed to load docx]');
    } else if (ext === '.xlsx' || ext === '.xls') {
      const rr = await window.fsapi.readBase64(p);
      if (rr.ok && rr.base64) {
        try {
          const wb = XLSX.read(rr.base64, { type: 'base64' });
          const sheets = wb.SheetNames.map((name) => ({ name, html: XLSX.utils.sheet_to_html(wb.Sheets[name]) }));
          const html = DOMPurify.sanitize(sheets.map((s) => `<h3>${s.name}</h3>${s.html}`).join('\n'));
          setContent(`__HTML_IFRAME__${html}`);
        } catch {
          setContent('[failed to render xlsx]');
        }
      } else setContent('[failed to load xlsx]');
    } else if (ext === '.csv') {
      const rr = await window.fsapi.read(p);
      if (rr.ok && rr.data !== undefined) {
        try {
          const parsed = Papa.parse<string[]>(rr.data, { skipEmptyLines: true });
          const rows = parsed.data as string[][];
          const header = rows[0] || [];
          const body = rows.slice(1);
          const STYLE = `<style>table{border-collapse:collapse;font-size:12px}th,td{border:1px solid #ccc;padding:4px 6px}tr:nth-child(even){background:#f7f7f7}</style>`;
          const esc = (s: string) => (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
          const html = `${STYLE}<table><thead><tr>${header
            .map((c) => `<th>${esc(c)}</th>`)
            .join('')}</tr></thead><tbody>${body
            .map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join('')}</tr>`)
            .join('')}</tbody></table>`;
          setContent(`__HTML_IFRAME__${html}`);
        } catch {
          setContent('[failed to parse csv]');
        }
      } else setContent('[failed to load csv]');
    } else if (ext === '.html' || ext === '.htm') {
      const rr = await window.fsapi.read(p);
      const html = rr.ok ? rr.data || '' : '';
      setContent(`__HTML_IFRAME__${DOMPurify.sanitize(html)}`);
    } else if (ext === '.md' || ext === '.mdx') {
      const rr = await window.fsapi.read(p);
      const html = (rr.ok ? marked.parse(rr.data || '') : '') as string;
      setContent(`__HTML_IFRAME__${DOMPurify.sanitize(html)}`);
    } else if (isTextExt(ext)) {
      const rr = await window.fsapi.read(p);
      setContent(rr.ok ? rr.data || '' : rr.error || '');
      if (rr.ok) {
        setDownloadUrl(`data:text/plain;charset=utf-8,${encodeURIComponent(rr.data || '')}`);
        setDownloadName(p.split(/[\\/]/).pop() || 'file.txt');
      }
    } else {
      setContent(`[preview not implemented for ${ext}]`);
    }
    try {
      const res = await window.idx.backlinks(p);
      setBacklinks(res.ok ? (res.backlinks || []) : []);
    } catch {
      setBacklinks([]);
    }
  };

  const humanCwd = useMemo(() => cwd.replace(/\\/g, '/'), [cwd]);

  return (
    <div className="flex-1 min-h-0 h-full flex p-6 gap-4 overflow-hidden">
      <div className="w-1/3 min-h-0 h-full bg-[var(--bg-secondary)] rounded-lg p-4 overflow-y-auto border border-[var(--border)]">
        <div className="flex items-center justify-between mb-3 gap-2">
          <div className="text-xs text-[var(--text-tertiary)] truncate" title={humanCwd}>
            {humanCwd}
          </div>
          <div className="flex gap-2">
            <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs" onClick={chooseDir}>
              Browse
            </button>
            <button
              className="px-2 py-1 rounded bg-[var(--accent)] text-white text-xs"
              onClick={useInChat}
              disabled={!cwd}
            >
              Use in Chat
            </button>
            <button
              className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs"
              disabled={!cwd}
              onClick={async () => {
                if (!cwd) return;
                setIndexStatus('Indexing...');
                const r = await window.idx.build(cwd);
                setIndexStatus(
                  r.ok ? `Indexed ${r.stats?.files} files / ${r.stats?.links} links` : r.error || 'Index error'
                );
                if (selected) {
                  const b = await window.idx.backlinks(selected);
                  setBacklinks(b.ok ? (b.backlinks || []) : []);
                }
              }}
            >
              Build Index
            </button>
            <button
              className={`px-2 py-1 rounded border text-xs ${
                watching
                  ? 'bg-green-500/20 border-green-500/40 text-green-200'
                  : 'bg-[var(--bg-tertiary)] border-[var(--border)] text-[var(--text-secondary)]'
              }`}
              disabled={!cwd}
              onClick={async () => {
                if (!watching) {
                  const r = await window.idx.watchStart(cwd);
                  if (r.ok) setWatching(true);
                } else {
                  await window.idx.watchStop();
                  setWatching(false);
                }
              }}
            >
              Watch: {watching ? 'on' : 'off'}
            </button>
          </div>
        </div>
        <div className="flex gap-2 mb-2">
          <button
            className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs"
            disabled={!cwd}
            onClick={async () => {
              const name = prompt('New file name (relative to cwd)');
              if (!name) return;
              const p = (cwd ? cwd : '') + (cwd.endsWith('/') || cwd.endsWith('\\') ? '' : '/') + name;
              const r = await window.fsapi.createFile(p, '');
              if (!r.ok) alert(r.error);
              else loadDir(cwd);
            }}
          >
            New File
          </button>
          <button
            className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs"
            disabled={!cwd}
            onClick={async () => {
              const name = prompt('New folder name (relative to cwd)');
              if (!name) return;
              const p = (cwd ? cwd : '') + (cwd.endsWith('/') || cwd.endsWith('\\') ? '' : '/') + name;
              const r = await window.fsapi.createDir(p);
              if (!r.ok) alert(r.error);
              else loadDir(cwd);
            }}
          >
            New Folder
          </button>
          <button
            className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs"
            disabled={!selected}
            onClick={async () => {
              const newName = prompt('Rename to (full path)', selected || '');
              if (!newName || !selected) return;
              const r = await window.fsapi.renamePath(selected, newName);
              if (!r.ok) alert(r.error);
              else {
                setSelected(newName);
                loadDir(cwd);
              }
            }}
          >
            Rename
          </button>
          <button
            className="px-2 py-1 rounded bg-red-500/20 border border-red-500/40 text-xs"
            disabled={!selected || !cwd}
            onClick={async () => {
              if (!selected || !cwd) return;
              if (!confirm(`Delete (move to .trash):\n${selected}?`)) return;
              const r = await window.fsapi.deletePath(selected, cwd);
              if (!r.ok) alert(r.error);
              else {
                setSelected(null);
                loadDir(cwd);
              }
            }}
          >
            Delete
          </button>
          <button
            className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs"
            onClick={async () => {
              const r = await window.fsapi.undo();
              if (!r.ok) alert(r.error);
              else if (cwd) loadDir(cwd);
            }}
          >
            Undo
          </button>
        </div>
        {indexStatus && <div className="text-2xs text-[var(--text-tertiary)] mb-2">{indexStatus}</div>}
        {error && <div className="text-xs text-red-300 mb-2">{error}</div>}
        <ul className="space-y-1">
          {cwd && cwd !== pathDir(cwd) && (
            <li
              className="cursor-pointer text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              onClick={() => setCwd(pathDir(cwd))}
            >
              ..
            </li>
          )}
          {entries.map((e) => (
            <li
              key={e.path}
              className="cursor-pointer flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              onClick={() => open(e.path)}
            >
              <span className={`inline-block w-2 h-2 rounded-full ${e.isDir ? 'bg-blue-400' : 'bg-gray-400'}`} />
              <span className="truncate">
                {e.name}
                {e.isDir ? '/' : ''}
              </span>
            </li>
          ))}
        </ul>
      </div>
      <div className="w-2/3 min-h-0 h-full bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border)] overflow-hidden flex flex-col">
        <div className="text-sm font-semibold mb-2 truncate">Preview: {selected || '(none)'}</div>
        <div className="bg-[var(--bg-tertiary)] p-3 rounded flex-1 min-h-0 overflow-auto border border-[var(--border)] relative">
          {downloadUrl && (
            <a
              href={downloadUrl}
              download={downloadName}
              className="absolute top-2 right-2 px-2 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border)] text-2xs"
            >
              Download
            </a>
          )}
          {selected && content.startsWith('__HTML_IFRAME__') ? (
            <iframe className="w-full h-full bg-white" sandbox="allow-same-origin" srcDoc={content.replace('__HTML_IFRAME__', '')} />
          ) : selected && pathExt(selected).toLowerCase() === '.pdf' ? (
            <iframe className="w-full h-full bg-white" src={content} />
          ) : selected && isTextExt(pathExt(selected).toLowerCase()) ? (
            <div className="prose prose-invert max-w-none text-sm">
              {pathExt(selected).toLowerCase() === '.md' ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              ) : (
                <pre className="hljs">
                  <code
                    dangerouslySetInnerHTML={{
                      __html: (() => {
                        try {
                          return hljs.highlightAuto(content || '').value;
                        } catch {
                          return content || '';
                        }
                      })(),
                    }}
                  />
                </pre>
              )}
            </div>
          ) : (
            <div className="text-[var(--text-tertiary)] text-sm">{content || 'Select a file to preview'}</div>
          )}
        </div>
        <div className="mt-3">
          <div className="text-sm font-semibold mb-1">Backlinks</div>
          {!selected || backlinks.length === 0 ? (
            <div className="text-2xs text-[var(--text-tertiary)]">
              {selected ? 'No backlinks found' : 'Select a file to see backlinks'}
            </div>
          ) : (
            <ul className="text-xs space-y-1">
              {backlinks.map((b, i) => (
                <li key={i} className="truncate flex items-center gap-2">
                  <button
                    className="underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                    onClick={() => open(b.from)}
                  >
                    {b.from}
                  </button>
                  {b.anchor ? (
                    <button
                      className="px-2 py-0.5 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] text-2xs"
                      onClick={() => {
                        const iframe = document.querySelector('iframe');
                        if (!iframe) return;
                        try {
                          const doc = (iframe as HTMLIFrameElement).contentDocument;
                          const target = doc?.getElementById(b.anchor!);
                          target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        } catch {}
                      }}
                    >
                      Jump #{b.anchor}
                    </button>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default FilesWorkspace;

