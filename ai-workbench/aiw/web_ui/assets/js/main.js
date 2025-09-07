window.App = window.App || {};
(function () {
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
          else {
            const res = JSON.parse(await App.backend.read_file(it.path));
            if (res.ok) {
              if (!window._cm) {
                try { window._cm = CodeMirror(App.qs('#editorMount'), { value: res.content, lineNumbers: true, mode: 'javascript' }); }
                catch { App.qs('#editorMount').textContent = res.content; }
              } else { window._cm.setValue(res.content); }
            }
          }
        };
        el.appendChild(line);
      });
    });
  }

  function bindApprovals() {
    App.qsa('#execModal [data-decision]').forEach(btn => btn.onclick = () => { App.backend.exec_approval(App._execEventId, btn.dataset.decision); App.ui.hide('#execModal'); });
    App.qsa('#patchModal [data-decision]').forEach(btn => btn.onclick = () => { App.backend.patch_approval(App._patchEventId, btn.dataset.decision); App.ui.hide('#patchModal'); });
  }

  window.addEventListener('DOMContentLoaded', () => {
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
    const refreshFs = App.qs('#refreshFs'); if (refreshFs) refreshFs.onclick = listDir;
    bindApprovals(); listDir();
  });
})();
