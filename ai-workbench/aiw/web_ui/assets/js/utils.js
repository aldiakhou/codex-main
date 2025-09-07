window.App = window.App || {};
(function () {
  const qs = (s, r = document) => r.querySelector(s);
  const qsa = (s, r = document) => Array.from(r.querySelectorAll(s));
  const log = (m) => {
    const el = qs('#logs');
    if (!el) return;
    el.textContent += `[${new Date().toLocaleTimeString()}] ${m}\n`;
    el.scrollTop = el.scrollHeight;
  };
  const status = (s) => {
    const dot = qs('#statusDot');
    const txt = qs('#statusText');
    if (txt) txt.textContent = s[0].toUpperCase() + s.slice(1);
    if (dot) dot.className = 'w-2.5 h-2.5 rounded-full ' + (s === 'connected' ? 'bg-emerald-500' : s === 'connecting' ? 'bg-amber-400' : 'bg-red-400');
    // Toggle start/stop buttons
    const start = qs('#startBtn'); const stop = qs('#stopBtn');
    if (start) { start.disabled = (s !== 'disconnected'); start.classList.toggle('opacity-50', start.disabled); start.classList.toggle('cursor-not-allowed', start.disabled); }
    if (stop) { stop.disabled = (s !== 'connected'); stop.classList.toggle('opacity-50', stop.disabled); stop.classList.toggle('cursor-not-allowed', stop.disabled); }
  };

  const ui = {
    addMsg(role, text) {
      const wrap = qs('#chat');
      if (!wrap) return;
      if (role === 'assistant' && App._lastAssistant?.isLive) {
        App._lastAssistant.body.textContent += text;
        wrap.scrollTop = wrap.scrollHeight;
        return;
      }
      const row = document.createElement('div');
      row.className = 'flex gap-2';
      const bubble = document.createElement('div');
      bubble.className = 'rounded px-3 py-2 max-w-[90%] whitespace-pre-wrap ' + (role === 'user' ? 'bg-indigo-50' : 'bg-gray-100');
      bubble.textContent = text;
      row.appendChild(bubble);
      wrap.appendChild(row);
      wrap.scrollTop = wrap.scrollHeight;
      App._lastAssistant = role === 'assistant' ? { body: bubble, isLive: true } : null;
    },
    endAssistantLive() { if (App._lastAssistant) App._lastAssistant.isLive = false; },
    setDiff(diff) { const el = qs('#diffView'); if (el) el.textContent = diff || ''; },
    appendTerminal(text) {
      const term = qs('#terminal'); if (!term) return;
      term.textContent += text; term.scrollTop = term.scrollHeight;
    },
    show(id) { const el = qs(id); if (!el) return; el.classList.remove('hidden'); el.classList.add('flex'); },
    hide(id) { const el = qs(id); if (!el) return; el.classList.add('hidden'); el.classList.remove('flex'); },
  };

  App.qs = qs; App.qsa = qsa; App.log = log; App.status = status; App.ui = ui; App.state = { termByCall: {} };
})();
