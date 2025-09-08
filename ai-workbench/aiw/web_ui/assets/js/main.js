window.App = window.App || {};
(function () {
  // Utility: run a callback once the backend bridge is ready
  function whenBackendReady(cb) {
    if (App.backend) { cb(); return; }
    let attempts = 0;
    const maxAttempts = 100; // ~10s at 100ms
    const timer = setInterval(() => {
      attempts++;
      if (App.backend) { clearInterval(timer); cb(); }
      else if (attempts >= maxAttempts) { clearInterval(timer); App.log('Backend not ready (timeout)'); }
    }, 100);
    // Also hook the explicit callback if available
    App.onBackendReady = () => { try { clearInterval(timer); cb(); } catch {} };
  }
  function send() {
    const text = App.qs('#composer').value.trim(); if (!text) return;
    App.ui.addMsg('user', text);
    const payload = {
      text,
      cwd: App.qs('#cwdInput')?.value.trim() || undefined,
      approval_policy: App.qs('#approvalSelect')?.value || 'on-request',
      sandbox_mode: App.qs('#sandboxSelect')?.value || 'read-only',
      model: App.qs('#modelSelect')?.value || 'gpt-5',
      effort: App.qs('#effortSelect')?.value || 'medium',
      summary: App.qs('#summarySelect')?.value || 'auto',
    };
    App.backend.send_user_turn_json(JSON.stringify(payload));
    App.qs('#composer').value = '';
  }

  function listDir_legacy1() {
    const cwd = App.qs('#cwdInput')?.value.trim() || '';
    App.backend.list_dir(cwd).then((s) => {
      const res = JSON.parse(s);
      const el = App.qs('#fsList'); if (!el) return;
      if (!res.ok) { el.textContent = res.error || 'Failed'; return; }
      el.innerHTML = '';
      res.items.sort((a,b)=> a.is_dir === b.is_dir ? a.name.localeCompare(b.name) : (a.is_dir? -1 : 1));
      res.items.forEach((it) => {
        const line = document.createElement('div');
        line.className = 'flex gap-2';
        line.innerHTML = `<span class="${it.is_dir?'text-primary':'text-muted'}">${it.is_dir?'↪':'📄'}</span><button class="text-left hover:underline" title="${it.path}">${it.name}</button>`;
        line.querySelector('button').onclick = async () => {
          if (it.is_dir) { App.qs('#cwdInput').value = it.path; App.listDir(); }
          else { await openFileInEditor(it.path); }
        };
        el.appendChild(line);
      });
    });
  }

  // Lucide-enhanced workspace listing used by UI triggers
  App.listDir = function () {
    const cwd = App.qs('#cwdInput')?.value.trim() || '';
    App.backend.list_dir(cwd).then((s) => {
      const res = JSON.parse(s);
      const el = App.qs('#fsList'); if (!el) return;
      if (!res.ok) { el.textContent = res.error || 'Failed'; return; }
      el.innerHTML = '';
      (res.items || [])
        .sort((a,b)=> a.is_dir === b.is_dir ? a.name.localeCompare(b.name) : (a.is_dir? -1 : 1))
        .forEach((it) => {
          const line = document.createElement('div');
          line.className = 'flex gap-2 items-center';
          const icon = document.createElement('i');
          icon.setAttribute('data-lucide', it.is_dir ? 'folder' : 'file');
          icon.className = 'w-4 h-4 ' + (it.is_dir ? 'text-violet-400' : 'text-gray-400');
          const btn = document.createElement('button');
          btn.className = 'text-left hover:underline truncate';
          btn.title = it.path;
          btn.textContent = it.name;
          btn.onclick = async () => {
            if (it.is_dir) { App.qs('#cwdInput').value = it.path; App.listDir(); }
            else { await openFileInEditor(it.path); }
          };
          line.appendChild(icon);
          line.appendChild(btn);
          el.appendChild(line);
        });
      try { if (window.lucide && typeof lucide.createIcons === 'function') { lucide.createIcons(); } } catch {}
    });
  }

  // Override listDir with a safer DOM construction to avoid unsafe innerHTML
  function listDir_legacy2() {
    const cwd = App.qs('#cwdInput')?.value.trim() || '';
    App.backend.list_dir(cwd).then((s) => {
      const res = JSON.parse(s);
      const el = App.qs('#fsList'); if (!el) return;
      if (!res.ok) { el.textContent = res.error || 'Failed'; return; }
      el.innerHTML = '';
      res.items
        .sort((a,b)=> a.is_dir === b.is_dir ? a.name.localeCompare(b.name) : (a.is_dir? -1 : 1))
        .forEach((it) => {
          const line = document.createElement('div');
          line.className = 'flex gap-2 items-center';
          const icon = document.createElement('span');
          icon.className = it.is_dir ? 'text-primary' : 'text-muted';
          icon.textContent = it.is_dir ? 'ðŸ“' : 'ðŸ“„';
          const btn = document.createElement('button');
          btn.className = 'text-left hover:underline truncate';
          btn.title = it.path;
          btn.textContent = it.name;
          btn.onclick = async () => {
            if (it.is_dir) { App.qs('#cwdInput').value = it.path; App.listDir(); }
            else { await openFileInEditor(it.path); }
          };
          line.appendChild(icon);
          line.appendChild(btn);
          el.appendChild(line);
        });
    });
  }

  function bindApprovals() {
    App.qsa('#execModal [data-decision]').forEach(btn => btn.onclick = () => { App.backend.exec_approval(App._execEventId, btn.dataset.decision); App.ui.hide('#execModal'); });
    App.qsa('#patchModal [data-decision]').forEach(btn => btn.onclick = () => { App.backend.patch_approval(App._patchEventId, btn.dataset.decision); App.ui.hide('#patchModal'); });
  }

  // --- Graph view ---------------------------------------------------------
  async function buildGraph() {
    try {
      const cwd = App.qs('#cwdInput')?.value.trim() || '';
      const res = JSON.parse(await App.backend.build_graph(cwd));
      if (!res.ok) { App.log('Graph build failed: ' + (res.error || 'unknown')); return; }
      renderGraph(res);
    } catch (e) { App.log('Graph error: ' + e); }
  }

  function renderGraph(data) {
    const mount = App.qs('#graphMount'); if (!mount) return;
    // Clear previous instance
    mount.innerHTML = '';
    if (typeof cytoscape === 'undefined') {
      const msg = document.createElement('div');
      msg.className = 'p-4 text-sm text-danger';
      msg.textContent = 'Cytoscape library not loaded. Check network and try again.';
      mount.appendChild(msg);
      return;
    }
    const cy = cytoscape({
      container: mount,
      elements: [...(data.nodes||[]), ...(data.edges||[])],
      style: [
        { selector: 'node', style: { 'label': 'data(label)', 'font-size': 10, 'background-color': '#6366f1', 'color': '#111827', 'text-wrap': 'wrap', 'text-max-width': '140px' } },
        { selector: 'edge', style: { 'width': 1.5, 'line-color': '#94a3b8', 'target-arrow-color': '#94a3b8', 'target-arrow-shape': 'triangle' } },
        { selector: 'node.selected', style: { 'background-color': '#10b981', 'border-width': 2, 'border-color': '#065f46' } },
        { selector: 'edge.related', style: { 'line-color': '#10b981', 'target-arrow-color': '#10b981', 'width': 2 } },
        { selector: 'node.faded', style: { 'opacity': 0.2 } }
      ],
      layout: { name: 'cose', padding: 20, animate: false }
    });
    // Cache graph for backlinks
    App.state = App.state || {};
    App.state.graph = {
      cy,
      nodes: (data.nodes||[]).map(n => n.data),
      edges: (data.edges||[]).map(e => e.data)
    };
    // Node click: select + open file
    cy.on('tap', 'node', async (evt) => {
      const id = evt.target.data('id');
      App.log('Open: ' + id);
      cy.elements().removeClass('selected');
      cy.elements().removeClass('related');
      evt.target.addClass('selected');
      evt.target.connectedEdges().addClass('related');
      updateBacklinks(id);
      await openFileInEditor(id);
    });
  }

  async function openFileInEditor(path) {
    try {
      const res = JSON.parse(await App.backend.read_file(path));
      if (!res.ok) { App.log('Open failed: ' + (res.error||'unknown')); return; }
      const text = res.content || '';
      // Switch to Code tab to edit
      const tabCodeBtn = App.qs('#tabCode'); if (tabCodeBtn) tabCodeBtn.click();
      const mount = App.qs('#editorMountCenter');
      const lang = guessMode(path);
      function createEditor(){
        if (!window._monacoEditor) {
          window._monacoModels = window._monacoModels || {};
          const uri = monaco.Uri.file(path);
          let model = monaco.editor.getModel(uri);
          if (!model) model = monaco.editor.createModel(text, lang, uri);
          window._monacoModels[path] = model;
          window._monacoEditor = monaco.editor.create(mount, {
            model,
            theme: document.body.classList.contains('theme-dark') ? 'vs-dark' : 'vs',
            automaticLayout: true,
            fontSize: 13,
            minimap: { enabled: false },
          });
          window._monacoEditor.onDidChangeCursorPosition(() => updateStatusBar(path));
          window._monacoEditor.onDidChangeModelContent(() => {
            if (window._mermaidTimer) clearTimeout(window._mermaidTimer);
            window._mermaidTimer = setTimeout(()=> updateMermaidPreview(window._monacoEditor.getValue()), 300);
          });
        } else {
          const uri = monaco.Uri.file(path);
          let model = monaco.editor.getModel(uri);
          if (!model) model = monaco.editor.createModel(text, lang, uri);
          window._monacoEditor.setModel(model);
        }
        App.state = App.state || {}; App.state.currentFile = path;
        ensureCodeTab(path);
        updateStatusBar(path);
        updateMermaidPreview(window._monacoEditor.getValue());
      }
      // Load Monaco via AMD loader (local path only) with single-boot guard
      if (typeof monaco === 'undefined') {
        if (typeof require !== 'undefined') {
          if (!window.__monacoConfigured) {
            try { require.config({ paths: { 'vs': './js/vendor/monaco/min/vs' } }); } catch {}
            window.__monacoConfigured = true;
          }
          const boot = () => { try { createEditor(); } catch(e) { App.log('Editor init error: ' + e); } };
          if (!window.__monacoLoading) {
            window.__monacoLoading = true;
            try { require(['vs/editor/editor.main'], () => { window.__monacoReady = true; boot(); }); }
            catch(e) { App.log('Monaco require failed: ' + e); }
          } else if (window.__monacoReady) {
            boot();
          } else {
            const t = setInterval(()=>{ if (window.__monacoReady) { clearInterval(t); boot(); } }, 60);
          }
        } else {
          mount.textContent = text;
        }
      } else { createEditor(); }
    } catch (e) { App.log('Editor error: ' + e); }
  }

  function updateBacklinks(id) {
    const panel = App.qs('#backlinksPanel'); if (!panel) return;
    const g = App.state?.graph; if (!g) { panel.textContent = '(no graph)'; return; }
    const incoming = g.edges.filter(e => e.target === id).map(e => e.source);
    const outgoing = g.edges.filter(e => e.source === id).map(e => e.target);
    const uniq = arr => Array.from(new Set(arr));
    const inc = uniq(incoming), out = uniq(outgoing);
    panel.innerHTML = '';
    const mk = (title, items) => {
      const h = document.createElement('div'); h.className = 'font-semibold mb-1'; h.textContent = title; panel.appendChild(h);
      if (!items.length) { const em=document.createElement('div'); em.className='text-muted mb-2'; em.textContent='(none)'; panel.appendChild(em); return; }
      items.forEach(p => {
        const row = document.createElement('div'); row.className='truncate mb-1 flex items-center gap-2';
        const btn = document.createElement('button'); btn.className='text-primary hover:underline text-left truncate'; btn.textContent = p.split(/[\\/]/).pop(); btn.title = p; btn.onclick = () => openFileInEditor(p);
        row.appendChild(btn); panel.appendChild(row);
      });
    };
    mk('Backlinks', inc); mk('Links', out);
  }

  function updateMermaidPreview(text) {
    const box = App.qs('#editorPreviewCenter'); if (!box) return;
    if (typeof mermaid === 'undefined') { box.textContent = '(Mermaid not loaded)'; return; }
    const fences = Array.from(text.matchAll(/```mermaid\s([\s\S]*?)```/g)).map(m => m[1]);
    if (!fences.length) { box.textContent = '(no mermaid blocks)'; return; }
    box.innerHTML = fences.map((code,i)=>`<div class="mb-2"><div class="mermaid" id="mmd_${i}">${code}</div></div>`).join('');
    try {
      mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });
      // v10: run to process .mermaid divs in container
      mermaid.run({ querySelector: '#editorPreviewCenter' });
    } catch (e) {
      box.textContent = 'Mermaid render error: ' + e;
    }
  }

  
  function buildApplyPatch(path, oldText, newText) {
    const rel = (path||'').replace(/\\/g, '/');
    const oldLines = (oldText||'').split('\n');
    const newLines = (newText||'').split('\n');
    const minus = oldLines.map(l => '-' + l).join('\n');
    const plus = newLines.map(l => '+' + l).join('\n');
    return `*** Begin Patch\n*** Update File: ${rel}\n@@\n${minus}\n${plus}\n*** End Patch`;
  }
  function guessMode(path) {
    const p = (path||'').toLowerCase();
    if (p.endsWith('.md') || p.endsWith('.markdown')) return 'markdown';
    if (p.endsWith('.ts') || p.endsWith('.tsx')) return 'typescript';
    if (p.endsWith('.js') || p.endsWith('.mjs') || p.endsWith('.cjs')) return 'javascript';
    if (p.endsWith('.json')) return {name:'javascript', json:true};
    if (p.endsWith('.sh') || p.endsWith('.bash')) return 'shell';
    if (p.endsWith('.py')) return 'python';
    if (p.endsWith('.yml') || p.endsWith('.yaml')) return 'yaml';
    if (p.endsWith('.toml')) return 'toml';
    if (p.endsWith('.ini') || p.endsWith('.cfg')) return 'ini';
    if (p.endsWith('.html') || p.endsWith('.htm')) return 'html';
    if (p.endsWith('.css')) return 'css';
    if (p.endsWith('.xml')) return 'xml';
    if (p.endsWith('.rs')) return 'rust';
    if (p.endsWith('.go')) return 'go';
    if (p.endsWith('.java')) return 'java';
    if (p.endsWith('.kt') || p.endsWith('.kts')) return 'kotlin';
    if (p.endsWith('.cs')) return 'csharp';
    if (p.endsWith('.php')) return 'php';
    if (p.endsWith('.rb')) return 'ruby';
    if (p.endsWith('.sql')) return 'sql';
    if (p.endsWith('.ps1')) return 'powershell';
    return 'markdown';
  }

  function updateStatusBar(path) {
    const p = App.qs('#statusPath'); const i = App.qs('#statusInfo');
    if (p) p.textContent = path || '';
    if (i && window._monacoEditor) {
      const pos = window._monacoEditor.getPosition();
      const model = window._monacoEditor.getModel();
      let eol = model && model.getEOL && model.getEOL();
      eol = eol === '\r\n' ? 'CRLF' : 'LF';
      const lang = model && model.getLanguageId ? model.getLanguageId() : 'text';
      i.textContent = `Ln ${pos.lineNumber}, Col ${pos.column} â€¢ ${lang} â€¢ ${eol}`;
    }
  }

  // --- Code tabs & Save ---------------------------------------------------
  function ensureCodeTab(path) {
    const tabs = App.qs('#codeTabs'); if (!tabs) return;
    const title = (path||'').split(/[\\/]/).pop();
    // Check existing
    let existing = Array.from(tabs.querySelectorAll('[data-path]')).find(e => e.dataset.path === path);
    if (!existing) {
      const pill = document.createElement('div');
      pill.dataset.path = path;
      pill.className = 'flex items-center gap-1 px-2 py-1 rounded bg-surface-2 cursor-pointer';
      pill.innerHTML = `<span class="truncate max-w-[200px]" title="${path}">${title}</span><button class="text-muted hover:text-danger" title="Close" data-close>Ã—</button>`;
      pill.onclick = (e) => { if ((e.target).dataset.close) return; openFileInEditor(path); };
      pill.querySelector('[data-close]').onclick = (e) => { e.stopPropagation(); pill.remove(); if (App.state.currentFile === path) App.state.currentFile = null; };
      tabs.appendChild(pill);
    }
    // Activate current
    tabs.querySelectorAll('[data-path]').forEach(el => el.classList.remove('tab-active'));
    existing = Array.from(tabs.querySelectorAll('[data-path]')).find(e => e.dataset.path === path);
    if (existing) existing.classList.add('tab-active');
    // persist recent
    try { App.backend.add_recent_file(path); } catch {}
  }


  window.addEventListener('DOMContentLoaded', () => {
    App.log('UI ready');
    App.initChannel();
    App.initSettings();
    // Render Lucide icons if available
    try { if (window.lucide && typeof lucide.createIcons === 'function') { lucide.createIcons(); } } catch {}
    // Theme init
    (function initTheme(){
      try {
        const stored = localStorage.getItem('aiw_theme');
        let theme = stored || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        document.body.classList.toggle('theme-dark', theme === 'dark');
        const btn = App.qs('#themeToggle'); if (btn) btn.onclick = () => {
          const cur = document.body.classList.contains('theme-dark') ? 'dark' : 'light';
          const next = cur === 'dark' ? 'light' : 'dark';
          document.body.classList.toggle('theme-dark', next === 'dark');
          localStorage.setItem('aiw_theme', next);
          try { App.applyAutoContrast && App.applyAutoContrast(); } catch {}
        };
      } catch {}
    })();
    const start = App.qs('#startBtn'); if (start) start.onclick = () => App.backend.start_backend();
    const stop = App.qs('#stopBtn'); if (stop) stop.onclick = () => App.backend.stop_backend();
    const login = App.qs('#loginBtn'); if (login) login.onclick = () => App.backend.login('');
    // Window controls
    const wmin = App.qs('#winMin'); if (wmin) wmin.onclick = () => { try { App.window && App.window.minimize(); } catch {} };
    const wmax = App.qs('#winMax'); if (wmax) wmax.onclick = () => { try { App.window && App.window.maximize_restore(); } catch {} };
    const wclose = App.qs('#winClose'); if (wclose) wclose.onclick = () => { try { App.window && App.window.close(); } catch {} };

    // Enable dragging the frameless window by grabbing the app header background
    const dragHost = App.qs('header.app-header');
    if (dragHost) {
      let lastX = 0, lastY = 0, dragging = false;
      const isInteractive = (el)=> !!el && (el.closest('button,select,input,textarea,a,[role="button"]'));
      const onMove = (e)=>{ if (!dragging) return; const dx = e.screenX - lastX, dy = e.screenY - lastY; lastX = e.screenX; lastY = e.screenY; try { App.window && App.window.move_by(dx, dy); } catch {} };
      const onUp = ()=>{
        if (!dragging) return;
        dragging = false;
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.body.style.cursor = '';
        // Snap to edges if near
        try {
          const margin = 24;
          const sw = (window.screen && window.screen.availWidth) || window.innerWidth;
          const sh = (window.screen && window.screen.availHeight) || window.innerHeight;
          if (lastX <= margin) { App.window && App.window.snap('left'); }
          else if (lastX >= sw - margin) { App.window && App.window.snap('right'); }
          else if (lastY <= margin) { App.window && App.window.snap('maximize'); }
        } catch {}
      };
      dragHost.addEventListener('mousedown', (e)=>{
        if (isInteractive(e.target)) return; // don't start drag from controls
        dragging = true; lastX = e.screenX; lastY = e.screenY; document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp); document.body.style.cursor = 'move';
      });
      dragHost.addEventListener('dblclick', (e)=>{ if (isInteractive(e.target)) return; try { App.window && App.window.maximize_restore(); } catch {} });
    }

    // Install window edge resizers for frameless mode
    (function installWindowResizers(){
      if (!App.window) return; // wait until channel binds window
      const edges = [
        { id:'edge-left',   edge:'left',        style:{ left:'0',   top:'0',    bottom:'0', width:'6px',  cursor:'ew-resize' } },
        { id:'edge-right',  edge:'right',       style:{ right:'0',  top:'0',    bottom:'0', width:'6px',  cursor:'ew-resize' } },
        { id:'edge-top',    edge:'top',         style:{ top:'0',    left:'0',   right:'0',  height:'6px', cursor:'ns-resize' } },
        { id:'edge-bottom', edge:'bottom',      style:{ bottom:'0', left:'0',   right:'0',  height:'6px', cursor:'ns-resize' } },
        { id:'edge-tl',     edge:'top-left',    style:{ top:'0',    left:'0',   width:'12px', height:'12px', cursor:'nwse-resize' } },
        { id:'edge-tr',     edge:'top-right',   style:{ top:'0',    right:'0',  width:'12px', height:'12px', cursor:'nesw-resize' } },
        { id:'edge-bl',     edge:'bottom-left', style:{ bottom:'0', left:'0',   width:'12px', height:'12px', cursor:'nesw-resize' } },
        { id:'edge-br',     edge:'bottom-right',style:{ bottom:'0', right:'0',  width:'12px', height:'12px', cursor:'nwse-resize' } },
      ];
      const make = (cfg)=>{
        const el = document.createElement('div');
        el.dataset.edge = cfg.edge; el.id = cfg.id; el.className = 'window-resizer'; el.style.position='fixed'; el.style.zIndex='80'; el.style.userSelect='none'; el.style.touchAction='none'; el.style.background='transparent';
        Object.assign(el.style, cfg.style);
        const onMove = (e)=>{ const dx = e.screenX - (el._lastX||e.screenX); const dy = e.screenY - (el._lastY||e.screenY); el._lastX = e.screenX; el._lastY = e.screenY; try { App.window && App.window.resize_edge(cfg.edge, dx, dy); } catch {} };
        const onUp = ()=>{ document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); document.body.style.cursor = ''; };
        el.addEventListener('mousedown', (e)=>{ el._lastX = e.screenX; el._lastY = e.screenY; document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp); document.body.style.cursor = cfg.style.cursor; });
        document.body.appendChild(el);
      };
      edges.forEach(make);
    })();
    const refreshTools = App.qs('#refreshTools'); if (refreshTools) refreshTools.onclick = () => {
      if (App._toolsRefreshing) return;
      App._toolsRefreshing = true;
      refreshTools.disabled = true;
      refreshTools.textContent = 'Refreshingâ€¦';
      refreshTools.classList.add('opacity-50','cursor-not-allowed');
      try { App.backend.list_mcp_tools(); } catch { /* noop */ }
    };
    const toolFilter = App.qs('#toolFilter'); if (toolFilter) toolFilter.addEventListener('input', () => {
      const list = App.qs('#mcpTools'); if (!list) return;
      const names = (App.state?.mcpToolNames || []).filter(n => n.toLowerCase().includes(toolFilter.value.toLowerCase()));
      list.innerHTML = '';
      names.forEach(name => {
        const item = document.createElement('div');
        item.className = 'flex items-center justify-between text-sm py-1 border-b last:border-0';
        item.innerHTML = `<div class=\"truncate pr-2\" title=\"${name}\">${name}</div>`+
          `<button class=\"px-2 py-0.5 btn-muted\" data-tool=\"${name}\">Prompt</button>`;
        item.querySelector('button').onclick = () => {
          const prompt = `Please use the MCP tool \`${name}\` with appropriate parameters to accomplish the task.`;
          App.ui.addMsg('user', prompt);
          App.backend.send_user_turn_json(JSON.stringify({ text: prompt }));
        };
        list.appendChild(item);
      });
    });
    const refreshHistory = App.qs('#refreshHistory'); if (refreshHistory) refreshHistory.onclick = () => App.backend.get_history();
    const sendBtn = App.qs('#sendBtn'); if (sendBtn) sendBtn.onclick = send;
    const interruptBtn = App.qs('#interruptBtn'); if (interruptBtn) interruptBtn.onclick = () => App.backend.interrupt();
    const refreshFs = App.qs('#refreshFs'); if (refreshFs) refreshFs.onclick = () => whenBackendReady(App.listDir);
    const togglePreview = App.qs('#togglePreview'); if (togglePreview) togglePreview.onclick = () => { const box=App.qs('#editorPreviewCenter'); if (box) box.classList.toggle('hidden'); };
    const saveFile = App.qs('#saveFile'); if (saveFile) saveFile.onclick = async () => {
      try {
        const path = App.state?.currentFile; if (!path) { App.log('No file selected'); return; }
        const content = window._monacoEditor ? window._monacoEditor.getValue() : '';
        const res = JSON.parse(await App.backend.write_file(path, content));
        if (res.ok) App.log('Saved: ' + path); else App.log('Save failed: ' + (res.error||'unknown'));
      } catch (e) { App.log('Save error: ' + e); }
    };
    const saveWithApproval = App.qs('#saveWithApproval'); if (saveWithApproval) saveWithApproval.onclick = () => App.openSaveApproval && App.openSaveApproval();
    const saveApproveBtn = App.qs('#saveApproveBtn');
    const saveCancelBtn = App.qs('#saveCancelBtn');
    const saveMeta = App.qs('#saveMeta');
    const saveModal = App.qs('#saveModal');
    App.openSaveApproval = async function() {
      try {
        const path = App.state?.currentFile; if (!path) { App.log('No file selected'); return; }
        const oldRes = JSON.parse(await App.backend.read_file(path));
        if (!oldRes.ok) { App.log('Read failed: ' + (oldRes.error||'unknown')); return; }
        const oldText = oldRes.content || '';
        const newText = window._monacoEditor ? window._monacoEditor.getValue() : '';
        const patch = buildApplyPatch(path, oldText, newText);
        App._pendingSave = { path, newText };
        if (saveMeta) saveMeta.textContent = path;
        const box = App.qs('#savePreview'); if (box) box.textContent = patch;
        if (saveModal) { saveModal.classList.remove('hidden'); saveModal.classList.add('flex'); }
      } catch (e) { App.log('Save (approval) error: ' + e); }
    };
    if (saveApproveBtn) saveApproveBtn.onclick = async () => {
      try {
        const p = App._pendingSave; if (!p) return;
        const res = JSON.parse(await App.backend.write_file(p.path, p.newText));
        if (res.ok) App.toast ? App.toast('Saved: ' + p.path) : App.log('Saved: ' + p.path); else App.toast ? App.toast('Save failed: ' + (res.error||'unknown')) : App.log('Save failed');
      } catch (e) { App.toast ? App.toast('Save error: ' + e) : App.log('Save error: ' + e); }
      finally { if (saveModal) { saveModal.classList.add('hidden'); saveModal.classList.remove('flex'); } App._pendingSave = null; }
    };
    if (saveCancelBtn) saveCancelBtn.onclick = () => { if (saveModal) { saveModal.classList.add('hidden'); saveModal.classList.remove('flex'); } App._pendingSave = null; };
    bindApprovals(); whenBackendReady(App.listDir);
    // Restore recent tabs
    whenBackendReady(async () => {
      try {
        const s = JSON.parse(await App.backend.get_recent_files());
        if (s.ok) {
          (s.files||[]).slice(0,5).forEach(f => ensureCodeTab(f));
          if (s.last) openFileInEditor(s.last);
        }
      } catch {}
    });
    // Tabs
    const tabChat = App.qs('#tabChat');
    const tabGraph = App.qs('#tabGraph');
    const tabCode = App.qs('#tabCode');
    const refreshGraph = App.qs('#refreshGraph');
    const graphSearch = App.qs('#graphSearch');
    const graphLayout = App.qs('#graphLayout');
    const graphFit = App.qs('#graphFit');
    const chatPane = App.qs('#chatPane');
    const graphPane = App.qs('#graphPane');
    const codePane = App.qs('#codePane');
    App.log(`Tabs present: chat=${!!tabChat} graph=${!!tabGraph} code=${!!tabCode} chatPane=${!!chatPane} graphPane=${!!graphPane} codePane=${!!codePane}`);
    if (tabChat && tabGraph && tabCode && chatPane && graphPane && codePane) {
      tabChat.onclick = () => {
        App.log('Switching to Chat');
      tabChat.classList.add('tab-active'); tabChat.classList.remove('tab-inactive');
      tabGraph.classList.remove('tab-active'); tabGraph.classList.add('tab-inactive');
      tabCode.classList.remove('tab-active'); tabCode.classList.add('tab-inactive');
        chatPane.classList.remove('hidden'); graphPane.classList.add('hidden'); codePane.classList.add('hidden');
        [refreshGraph, graphSearch, graphLayout, graphFit].forEach(el => el && el.classList.add('hidden'));
      };
      tabGraph.onclick = () => {
        App.log('Switching to Graph');
      tabGraph.classList.add('tab-active'); tabGraph.classList.remove('tab-inactive');
      tabChat.classList.remove('tab-active'); tabChat.classList.add('tab-inactive');
      tabCode.classList.remove('tab-active'); tabCode.classList.add('tab-inactive');
        chatPane.classList.add('hidden'); graphPane.classList.remove('hidden'); codePane.classList.add('hidden');
        [refreshGraph, graphSearch, graphLayout, graphFit].forEach(el => el && el.classList.remove('hidden'));
        whenBackendReady(buildGraph);
      };
      tabCode.onclick = () => {
        App.log('Switching to Code');
      tabCode.classList.add('tab-active'); tabCode.classList.remove('tab-inactive');
      tabChat.classList.remove('tab-active'); tabChat.classList.add('tab-inactive');
      tabGraph.classList.remove('tab-active'); tabGraph.classList.add('tab-inactive');
        chatPane.classList.add('hidden'); graphPane.classList.add('hidden'); codePane.classList.remove('hidden');
        [refreshGraph, graphSearch, graphLayout, graphFit].forEach(el => el && el.classList.add('hidden'));
      };
      if (refreshGraph) refreshGraph.onclick = () => whenBackendReady(buildGraph);
      if (graphFit) graphFit.onclick = () => { const cy = App.state?.graph?.cy; if (cy) cy.fit(); };
      if (graphLayout) graphLayout.onchange = () => { const cy = App.state?.graph?.cy; if (!cy) return; const name = graphLayout.value||'cose'; cy.layout({ name, padding: 20, animate: false }).run(); };
      if (graphSearch) graphSearch.oninput = () => {
        const cy = App.state?.graph?.cy; if (!cy) return;
        const q = (graphSearch.value||'').toLowerCase();
        cy.nodes().forEach(n => {
          const label = (n.data('label')||'').toLowerCase();
          if (!q || label.includes(q)) n.removeClass('faded'); else n.addClass('faded');
        });
      };
    }

    // Resizers: persist left/center/right widths
    (function initResizers(){
      const grid = App.qs('#mainGrid'); if (!grid) return;
      function setCols(l,c,r){ grid.style.gridTemplateColumns = `${l} 6px ${c} 6px ${r}`; }
      function columnGapPx(){ const cs = window.getComputedStyle(grid); const g = parseFloat(cs.columnGap||'0'); return isNaN(g)?0:g; }
      function availablePx(){
        const resizers = 12; // two resizers
        const gaps = columnGapPx() * 4; // five tracks -> four gaps
        return Math.max(0, grid.clientWidth - resizers - gaps);
      }
      function normalizePxColumns(){
        const parts = grid.style.gridTemplateColumns.split(' 6px ');
        if (parts.length!==3) return;
        const toPx = (v)=> v.endsWith('px') ? parseFloat(v) : NaN;
        let L = toPx(parts[0]), C = toPx(parts[1]), R = toPx(parts[2]);
        if ([L,C,R].some(x=>isNaN(x))) return; // only normalize px-defined layouts
        const minL = 240, minC = 480, minR = 260;
        const avail = availablePx();
        const total = L + C + R;
        if (total <= 0 || avail <= 0) return;
        let scale = avail / total;
        let l = Math.max(minL, Math.round(L * scale));
        let c = Math.max(minC, Math.round(C * scale));
        let r = Math.max(minR, Math.round(R * scale));
        let sum = l + c + r;
        if (sum > avail) {
          let over = sum - avail;
          const trim = (cur, min)=>{ const d = Math.min(over, Math.max(0, cur-min)); over -= d; return cur - d; };
          c = trim(c, minC);
          r = trim(r, minR);
          l = trim(l, minL);
        }
        setCols(`${l}px`, `${c}px`, `${r}px`);
      }
      function loadCols(){
        try { App.backend.get_layout_state().then(s=>{ const j=JSON.parse(s); if(j.ok && j.state){ const st=j.state; setCols(st.left||'1fr', st.center||'2fr', st.right||'1fr'); normalizePxColumns(); } else { initPx(); } }); } catch{ initPx(); }
      }
      function saveCols(){
        const parts = grid.style.gridTemplateColumns.split(' 6px ');
        if (parts.length===3) {
          const payload = JSON.stringify({ left: parts[0].trim(), center: parts[1].trim(), right: parts[2].trim() });
          try { App.backend.set_layout_state(payload); } catch{}
        }
      }
      function makeDraggable(resizer, leftIdx){
        if (!resizer) return;
        let startX, startLeft, startCenter;
        const onMove = (e)=>{
          const dx = e.clientX - startX;
          const parts = grid.style.gridTemplateColumns.split(' 6px ');
          const left = parseFloat(startLeft), center = parseFloat(startCenter);
          const newLeft = Math.max(220, left + dx);
          const newCenter = Math.max(320, center - dx);
          parts[leftIdx] = `${newLeft}px`;
          parts[leftIdx+1] = `${newCenter}px`;
          setCols(parts[0], parts[1], parts[2]);
        };
        const onUp = ()=>{
          document.removeEventListener('pointermove', onMove);
          document.removeEventListener('pointerup', onUp);
          try { resizer.classList.remove('resizing'); document.body.style.cursor = 'default'; } catch {}
          saveCols();
        };
        resizer.addEventListener('pointerdown', (e)=>{
          const cols = window.getComputedStyle(grid).gridTemplateColumns.split(' 6px ');
          startX = e.clientX; startLeft = cols[leftIdx].replace('px',''); startCenter = cols[leftIdx+1].replace('px','');
          try { resizer.classList.add('resizing'); document.body.style.cursor = 'col-resize'; } catch {}
          document.addEventListener('pointermove', onMove); document.addEventListener('pointerup', onUp);
        });
      }
      const rl = App.qs('#resizerLeft'); const rr = App.qs('#resizerRight');
      // Initialize default px widths for smooth dragging, then load saved
      const initPx = ()=>{
        const w = availablePx();
        const minL = 240, minC = 480, minR = 260;
        let l = Math.max(minL, Math.round(w*0.22));
        let c = Math.max(minC, Math.round(w*0.56));
        let r = Math.max(minR, Math.round(w*0.22));
        let sum = l + c + r;
        if (sum > w) {
          let over = sum - w;
          const trim = (cur, min)=>{ const d = Math.min(over, Math.max(0, cur-min)); over -= d; return cur - d; };
          c = trim(c, minC);
          r = trim(r, minR);
          l = trim(l, minL);
        }
        setCols(`${l}px`, `${c}px`, `${r}px`);
      };
      initPx(); loadCols();
      makeDraggable(rl, 0);
      makeDraggable(rr, 1);
      window.addEventListener('resize', ()=>{ normalizePxColumns(); saveCols(); });
    })();
  });
})();
