window.App = window.App || {};
(function () {
  const show = (id) => { const el = App.qs(id); if (!el) return; el.classList.remove('hidden'); el.classList.add('flex'); };
  const hide = (id) => { const el = App.qs(id); if (!el) return; el.classList.add('hidden'); el.classList.remove('flex'); };

  App.openSettings = async function () {
    try {
      const res = JSON.parse(await App.backend.get_backend_config());
      if (res.ok) {
        const b = res.backend || {};
        App.qs('#setCodexPath').value = b.codex_path || '';
        App.qs('#setProfile').value = b.profile || '';
        App.qs('#setTimeout').value = b.timeout ?? 300;
        App.qs('#setRetries').value = b.max_retries ?? 3;
        App.qs('#setLogLevel').value = b.log_level || 'info';
      }
    } catch (e) { App.log('Failed to load settings: ' + e); }
    show('#settingsModal');
  };

  App.initSettings = function () {
    const btn = App.qs('#settingsBtn'); if (btn) btn.onclick = () => App.openSettings();
    const cancel = App.qs('#settingsCancel'); if (cancel) cancel.onclick = () => hide('#settingsModal');
    const save = App.qs('#settingsSave');
    if (save) save.onclick = async () => {
      const payload = {
        codex_path: App.qs('#setCodexPath').value.trim() || null,
        profile: App.qs('#setProfile').value.trim() || null,
        timeout: parseInt(App.qs('#setTimeout').value, 10) || 300,
        max_retries: parseInt(App.qs('#setRetries').value, 10) || 3,
        log_level: App.qs('#setLogLevel').value || 'info',
      };
      const res = JSON.parse(await App.backend.set_backend_config(JSON.stringify(payload)));
      if (!res.ok) { App.log('Save failed: ' + (res.error || 'unknown')); return; }
      App.log('Settings saved'); hide('#settingsModal');
    };

    const detect = App.qs('#detectCodex'); if (detect) detect.onclick = async () => {
      const res = JSON.parse(await App.backend.detect_codex_path());
      if (res.ok && res.codex_path) { App.qs('#setCodexPath').value = res.codex_path; App.log('Detected codex at ' + res.codex_path); }
      else { App.log('Detect failed: ' + (res.error || 'not found')); }
    };

    const browse = App.qs('#browseCodex'); if (browse) browse.onclick = async () => {
      const res = JSON.parse(await App.backend.browse_for_codex());
      if (res.ok && res.codex_path) { App.qs('#setCodexPath').value = res.codex_path; }
    };
  };
})();

