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
      // Load servers list
      try {
        const s = JSON.parse(await App.backend.get_mcp_servers());
        if (s.ok) App.renderServers(s.servers || {}, s.errors || {});
      } catch (e) { App.log('Failed to load servers: ' + e); }
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

    // Servers UI
    function parseArgs(input) {
      if (!input) return [];
      const tokens = input.match(/(\"[^\"]*\"|'[^']*'|\S)+/g) || [];
      return tokens.map(t => {
        if ((t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'"))) {
          return t.slice(1, -1);
        }
        return t;
      });
    }
    function parseEnv(input) {
      const env = {};
      if (!input) return env;
      input.split(';').map(s => s.trim()).filter(Boolean).forEach(pair => {
        const eq = pair.indexOf('='); if (eq>0) env[pair.slice(0,eq).trim()] = pair.slice(eq+1).trim();
      });
      return env;
    }

    App._renderServersData = { servers: {}, errors: {} };

    App.renderServers = function (servers, errors) {
      const wrap = App.qs('#serversList'); if (!wrap) return;
      wrap.innerHTML = '';
      App._renderServersData = { servers: servers||{}, errors: errors||{} };
      const entries = Object.entries(servers || {});
      if (!entries.length) {
        wrap.innerHTML = '<div class="text-xs text-gray-500 p-2">No servers configured.</div>';
        return;
      }
      entries.forEach(([name, s]) => {
        wrap.appendChild(App._renderServerRow(name, s, errors && errors[name]));
      });
    };

    App._renderServerRow = function(name, s, err) {
      const row = document.createElement('div');
      row.className = 'grid grid-cols-7 gap-2 items-center text-xs p-2 border-b last:border-0';
      row.innerHTML = `
        <div class="col-span-1 font-medium truncate" title="${name}">${name}</div>
        <div class="col-span-2 truncate" title="${s.command||''}">${s.command||''}</div>
        <div class="col-span-2 truncate" title="${(s.args||[]).join(' ')}">${(s.args||[]).join(' ')}</div>
        <div class="col-span-1 truncate" title="${Object.keys(s.env||{}).join(', ')}">${Object.keys(s.env||{}).length} env</div>
        <div class="col-span-1 text-right space-x-2">
          <button class="text-blue-600 hover:underline" data-act="edit">Edit</button>
          <button class="text-red-600 hover:underline" data-act="remove">Remove</button>
        </div>`;
      if (err) {
        const warn = document.createElement('div');
        warn.className = 'col-span-7 text-[11px] text-red-600 mt-1 truncate';
        warn.textContent = `Error: ${err}`;
        row.appendChild(warn);
      }
      row.querySelector('[data-act="remove"]').addEventListener('click', async () => {
        const ok = confirm(`Remove server ${name}?`);
        if (!ok) return;
        const res = JSON.parse(await App.backend.delete_mcp_server(name));
        if (res.ok) {
          const s2 = JSON.parse(await App.backend.get_mcp_servers());
          if (s2.ok) App.renderServers(s2.servers || {}, s2.errors || {});
        } else { App.log('Remove failed: ' + (res.error || 'unknown')); }
      });
      row.querySelector('[data-act="edit"]').addEventListener('click', () => {
        App._editServerRow(row, name, s);
      });
      return row;
    };

    App._editServerRow = function(row, oldName, s) {
      const nameVal = oldName || '';
      const cmdVal = s?.command || '';
      const argsVal = (s?.args||[]).map(a => (a.includes(' ') ? '"'+a+'"' : a)).join(' ');
      const envVal = Object.entries(s?.env||{}).map(([k,v]) => `${k}=${v}`).join(';');
      row.classList.add('bg-yellow-50');
      row.innerHTML = `
        <div class="col-span-1"><input class="border rounded px-1 py-0.5 w-full" value="${nameVal}" placeholder="name" /></div>
        <div class="col-span-2"><input class="border rounded px-1 py-0.5 w-full" value="${cmdVal}" placeholder="command" /></div>
        <div class="col-span-2"><input class="border rounded px-1 py-0.5 w-full" value="${argsVal}" placeholder="args (space-separated)" /></div>
        <div class="col-span-1"><input class="border rounded px-1 py-0.5 w-full" value="${envVal}" placeholder="KEY=VAL;KEY2=VAL2" /></div>
        <div class="col-span-1 text-right space-x-2">
          <button class="px-2 py-0.5 bg-emerald-600 text-white rounded" data-act="save">Save</button>
          <button class="px-2 py-0.5 bg-gray-200 rounded" data-act="cancel">Cancel</button>
        </div>`;
      const inputs = row.querySelectorAll('input');
      const nameInput = inputs[0], cmdInput = inputs[1], argsInput = inputs[2], envInput = inputs[3];
      row.querySelector('[data-act="cancel"]').addEventListener('click', async () => {
        const s2 = JSON.parse(await App.backend.get_mcp_servers());
        if (s2.ok) App.renderServers(s2.servers || {}, s2.errors || {});
      });
      row.querySelector('[data-act="save"]').addEventListener('click', async () => {
        const newName = (nameInput.value||'').trim();
        const command = (cmdInput.value||'').trim();
        if (!newName || !command) { App.log('Name and command are required'); return; }
        const args = parseArgs((argsInput.value||'').trim());
        const env = parseEnv((envInput.value||'').trim());
        if (oldName && newName !== oldName) {
          const del = JSON.parse(await App.backend.delete_mcp_server(oldName));
          if (!del.ok) { App.log('Rename failed (delete): ' + (del.error||'unknown')); return; }
        }
        const payload = { name: newName, command, args, env };
        const res = JSON.parse(await App.backend.upsert_mcp_server(JSON.stringify(payload)));
        if (res.ok) {
          const s2 = JSON.parse(await App.backend.get_mcp_servers());
          if (s2.ok) App.renderServers(s2.servers || {}, s2.errors || {});
        } else {
          App.log('Save failed: ' + (res.error || 'unknown'));
        }
      });
    };

    const addBtn = App.qs('#addServerBtn'); if (addBtn) addBtn.onclick = async () => {
      const wrap = App.qs('#serversList'); if (!wrap) return;
      const temp = document.createElement('div');
      temp.className = 'grid grid-cols-7 gap-2 items-center text-xs p-2 border-b bg-yellow-50';
      wrap.prepend(temp);
      App._editServerRow(temp, '', { command: '', args: [], env: {} });
    };

    const applyBtn = App.qs('#applyServersBtn'); if (applyBtn) applyBtn.onclick = async () => {
      App.log('Restarting backend to apply MCP server changes...');
      try { await App.backend.restart_backend(); } catch {}
    };
  };
})();
