window.App = window.App || {};
(function () {
  function decodeChunk(chunk) {
    if (Array.isArray(chunk)) {
      try { return new TextDecoder('utf-8', { fatal: false }).decode(new Uint8Array(chunk)); } catch { return ''; }
    }
    return typeof chunk === 'string' ? chunk : '';
  }

  App.onEvent = function (e) {
    switch (e.type) {
      case 'session_configured':
        App.status('connected');
        App.log(`Session configured. model=${e.model}`);
        // Auto-refresh MCP tools on session start
        if (App.backend && App.backend.list_mcp_tools) {
          try { App._toolsRefreshing = true; App.backend.list_mcp_tools(); } catch {}
        }
        // Clear server status
        const ss = App.qs('#serverStatus'); if (ss) ss.textContent = '';
        break;
      case 'agent_message_delta':
        App.ui.addMsg('assistant', e.delta || '');
        break;
      case 'agent_message':
        App.ui.addMsg('assistant', e.message || '');
        App.ui.endAssistantLive();
        break;
      case 'token_count': {
        const total = e.total_tokens ?? 0;
        const input = (e.input_tokens ?? 0) - (e.cached_input_tokens ?? 0);
        const output = e.output_tokens ?? 0;
        const reasoning = e.reasoning_output_tokens ?? 0;
        const el = App.qs('#tokenInfo');
        if (el) el.textContent = `Tokens: total=${total} input=${input} output=${output}${reasoning ? ` (reasoning ${reasoning})` : ''}`;
        break;
      }
      case 'turn_diff':
        App.ui.setDiff(e.unified_diff || '');
        break;
      case 'exec_command_begin':
        App.state.termByCall[e.call_id] = true; break;
      case 'exec_command_output_delta':
        App.ui.appendTerminal(decodeChunk(e.chunk));
        break;
      case 'exec_approval_request':
        App.qs('#execPreview').textContent = `$ cd ${e.cwd}\n$ ` + (e.command || []).join(' ');
        App._execEventId = e.id; App.ui.show('#execModal');
        break;
      case 'apply_patch_approval_request': {
        let preview = '';
        if (e.changes) {
          Object.entries(e.changes).forEach(([path, change]) => {
            if (change.type === 'add') preview += `=== ${path} (add) ===\n` + (change.content || '') + '\n\n';
            else if (change.type === 'delete') preview += `=== ${path} (delete) ===\n`;
            else if (change.type === 'update') preview += `=== ${path} (update) ===\n` + (change.unified_diff || '') + '\n\n';
          });
        }
        App.qs('#patchPreview').textContent = preview || '(no changes)';
        App._patchEventId = e.id; App.ui.show('#patchModal');
        break; }
      case 'patch_apply_begin':
        App.log('Patch apply started'); break;
      case 'patch_apply_end':
        App.log(`Patch apply ${e.success ? 'succeeded' : 'failed'}`);
        if (e.stdout) App.ui.appendTerminal(e.stdout);
        if (e.stderr) App.ui.appendTerminal(e.stderr);
        break;
      case 'plan_update': {
        const el = App.qs('#plan'); if (el) el.textContent = JSON.stringify(e, null, 2); break; }
      case 'mcp_list_tools_response': {
        const list = App.qs('#mcpTools'); if (!list) break;
        const btn = App.qs('#refreshTools');
        if (btn) { btn.disabled = false; btn.textContent = 'Refresh'; btn.classList.remove('opacity-50','cursor-not-allowed'); }
        App._toolsRefreshing = false;
        // Cache tools for filtering
        App.state = App.state || {}; App.state.mcpToolNames = (e.tools ? Object.keys(e.tools) : []).sort();
        const filter = (App.qs('#toolFilter')?.value || '').toLowerCase();
        const names = App.state.mcpToolNames.filter(n => n.toLowerCase().includes(filter));
        list.innerHTML = '';
        names.forEach(name => {
          const item = document.createElement('div');
          item.className = 'flex items-center justify-between text-sm py-1 border-b last:border-0';
          item.innerHTML = `<div class="truncate pr-2" title="${name}">${name}</div>`+
            `<button class="px-2 py-0.5 btn-muted" data-tool="${name}">Prompt</button>`;
          item.querySelector('button').onclick = () => {
            const prompt = `Please use the MCP tool \`${name}\` with appropriate parameters to accomplish the task.`;
            App.ui.addMsg('user', prompt);
            App.backend.send_user_turn_json(JSON.stringify({ text: prompt }));
          };
          list.appendChild(item);
        });
        // Server status summary from qualified names
        const ss = App.qs('#serverStatus');
        if (ss) {
          const counts = {};
          (App.state.mcpToolNames || []).forEach(n => {
            const ix = n.indexOf('__'); if (ix>0) { const srv = n.slice(0, ix); counts[srv]=(counts[srv]||0)+1; }
          });
          const lines = Object.keys(counts).sort().map(k => `Server ${k}: ${counts[k]} tools`);
          ss.textContent = lines.length ? lines.join('\n') + '\n' : '';
        }
        break; }
      case 'error': {
        // Show errors (including MCP startup) in logs and server panel
        if (e.message) App.log(`Error: ${e.message}`);
        const m = /MCP client for `([^`]+)` failed to start: (.*)/.exec(e.message||'');
        if (m) {
          const [_, name, err] = m;
          const ss = App.qs('#serverStatus');
          if (ss) ss.textContent += `Server ${name}: ERROR ${err}\n`;
        }
        break; }
      case 'conversation_history': {
        const panel = App.qs('#historyPanel'); if (!panel) break;
        panel.textContent = JSON.stringify(e, null, 2);
        break; }
      case 'stream_error': App.log(`Stream error: ${e.message}`); break;
      case 'turn_aborted': App.log('Turn aborted'); break;
      default: break;
    }
  };
})();

