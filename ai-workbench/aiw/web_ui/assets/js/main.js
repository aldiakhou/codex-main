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
        line.querySelector('button').onclick = () => { if (it.is_dir) { App.qs('#cwdInput').value = it.path; listDir(); } };
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
    const sendBtn = App.qs('#sendBtn'); if (sendBtn) sendBtn.onclick = send;
    const interruptBtn = App.qs('#interruptBtn'); if (interruptBtn) interruptBtn.onclick = () => App.backend.interrupt();
    const refreshFs = App.qs('#refreshFs'); if (refreshFs) refreshFs.onclick = listDir;
    bindApprovals(); listDir();
  });
})();

