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

  function listDir() {
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
        line.innerHTML = `<span class="${it.is_dir?'text-indigo-600':'text-gray-600'}">${it.is_dir?'📁':'📄'}</span><button class="text-left hover:underline" title="${it.path}">${it.name}</button>`;
        line.querySelector('button').onclick = async () => {
          if (it.is_dir) { App.qs('#cwdInput').value = it.path; listDir(); }
          else { await openFileInEditor(it.path); }
        };
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
      msg.className = 'p-4 text-sm text-red-600';
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
      if (!window._cm) {
        try { window._cm = CodeMirror(mount, { value: text, lineNumbers: true, mode: guessMode(path) }); }
        catch { mount.textContent = text; }
      } else { window._cm.setValue(text); window._cm.setOption('mode', guessMode(path)); }
      if (window._cm && window._cm.setSize) { window._cm.setSize(null, '100%'); }
      App.state = App.state || {}; App.state.currentFile = path;
      ensureCodeTab(path);
      updateMermaidPreview(text);
      if (window._cm) {
        if (window._cm._debouncedPrev) clearTimeout(window._cm._debouncedPrev);
        window._cm.on('change', () => {
          if (window._cm._debouncedPrev) clearTimeout(window._cm._debouncedPrev);
          window._cm._debouncedPrev = setTimeout(() => updateMermaidPreview(window._cm.getValue()), 300);
        });
      }
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
      if (!items.length) { const em=document.createElement('div'); em.className='text-gray-500 mb-2'; em.textContent='(none)'; panel.appendChild(em); return; }
      items.forEach(p => {
        const row = document.createElement('div'); row.className='truncate mb-1 flex items-center gap-2';
        const btn = document.createElement('button'); btn.className='text-indigo-600 hover:underline text-left truncate'; btn.textContent = p.split(/[\\/]/).pop(); btn.title = p; btn.onclick = () => openFileInEditor(p);
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
    return *** Begin Patch\n*** Update File: \n@@\n\n\n*** End Patch;
  }function guessMode(path) {
    const p = (path||'').toLowerCase();
    if (p.endsWith('.md') || p.endsWith('.markdown')) return 'markdown';
    if (p.endsWith('.ts') || p.endsWith('.tsx')) return 'javascript';
    if (p.endsWith('.js') || p.endsWith('.mjs') || p.endsWith('.cjs')) return 'javascript';
    if (p.endsWith('.json')) return {name:'javascript', json:true};
    if (p.endsWith('.sh') || p.endsWith('.bash')) return 'shell';
    return 'markdown';
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
      pill.className = 'flex items-center gap-1 px-2 py-1 rounded bg-gray-100 cursor-pointer hover:bg-gray-200';
      pill.innerHTML = `<span class="truncate max-w-[200px]" title="${path}">${title}</span><button class="text-gray-500 hover:text-red-600" title="Close" data-close>×</button>`;
      pill.onclick = (e) => { if ((e.target).dataset.close) return; openFileInEditor(path); };
      pill.querySelector('[data-close]').onclick = (e) => { e.stopPropagation(); pill.remove(); if (App.state.currentFile === path) App.state.currentFile = null; };
      tabs.appendChild(pill);
    }
    // Activate current
    tabs.querySelectorAll('[data-path]').forEach(el => el.classList.remove('bg-indigo-600','text-white'));
    existing = Array.from(tabs.querySelectorAll('[data-path]')).find(e => e.dataset.path === path);
    if (existing) existing.classList.add('bg-indigo-600','text-white');
    // persist recent
    try { App.backend.add_recent_file(path); } catch {}
  }


  window.addEventListener('DOMContentLoaded', () => {
    App.log('UI ready');
    App.initChannel();
    App.initSettings();
    const start = App.qs('#startBtn'); if (start) start.onclick = () => App.backend.start_backend();
    const stop = App.qs('#stopBtn'); if (stop) stop.onclick = () => App.backend.stop_backend();
    const login = App.qs('#loginBtn'); if (login) login.onclick = () => App.backend.login('');
    const refreshTools = App.qs('#refreshTools'); if (refreshTools) refreshTools.onclick = () => {
      if (App._toolsRefreshing) return;
      App._toolsRefreshing = true;
      refreshTools.disabled = true;
      refreshTools.textContent = 'Refreshing…';
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
          `<button class=\"px-2 py-0.5 bg-gray-100 rounded hover:bg-gray-200\" data-tool=\"${name}\">Prompt</button>`;
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
    const refreshFs = App.qs('#refreshFs'); if (refreshFs) refreshFs.onclick = () => whenBackendReady(listDir);
    const togglePreview = App.qs('#togglePreview'); if (togglePreview) togglePreview.onclick = () => { const box=App.qs('#editorPreviewCenter'); if (box) box.classList.toggle('hidden'); };
    const saveFile = App.qs('#saveFile'); if (saveFile) saveFile.onclick = async () => {
      try {
        const path = App.state?.currentFile; if (!path) { App.log('No file selected'); return; }
        const content = window._cm ? window._cm.getValue() : '';
        const res = JSON.parse(await App.backend.write_file(path, content));
        if (res.ok) App.log('Saved: ' + path); else App.log('Save failed: ' + (res.error||'unknown'));
      } catch (e) { App.log('Save error: ' + e); }
    };
    const saveWithApproval = App.qs('#saveWithApproval'); if (saveWithApproval) saveWithApproval.onclick = () => App.openSaveApproval && App.openSaveApproval();
    bindApprovals(); whenBackendReady(listDir);
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
        tabChat.classList.add('bg-indigo-600','text-white'); tabChat.classList.remove('bg-gray-200');
        tabGraph.classList.remove('bg-indigo-600','text-white'); tabGraph.classList.add('bg-gray-200');
        tabCode.classList.remove('bg-indigo-600','text-white'); tabCode.classList.add('bg-gray-200');
        chatPane.classList.remove('hidden'); graphPane.classList.add('hidden'); codePane.classList.add('hidden');
        [refreshGraph, graphSearch, graphLayout, graphFit].forEach(el => el && el.classList.add('hidden'));
      };
      tabGraph.onclick = () => {
        App.log('Switching to Graph');
        tabGraph.classList.add('bg-indigo-600','text-white'); tabGraph.classList.remove('bg-gray-200');
        tabChat.classList.remove('bg-indigo-600','text-white'); tabChat.classList.add('bg-gray-200');
        tabCode.classList.remove('bg-indigo-600','text-white'); tabCode.classList.add('bg-gray-200');
        chatPane.classList.add('hidden'); graphPane.classList.remove('hidden'); codePane.classList.add('hidden');
        [refreshGraph, graphSearch, graphLayout, graphFit].forEach(el => el && el.classList.remove('hidden'));
        whenBackendReady(buildGraph);
      };
      tabCode.onclick = () => {
        App.log('Switching to Code');
        tabCode.classList.add('bg-indigo-600','text-white'); tabCode.classList.remove('bg-gray-200');
        tabChat.classList.remove('bg-indigo-600','text-white'); tabChat.classList.add('bg-gray-200');
        tabGraph.classList.remove('bg-indigo-600','text-white'); tabGraph.classList.add('bg-gray-200');
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
  });
})();

