window.App = window.App || {};
(function () {
  function bindBackend(b) {
    App.backend = b;
    b.status_changed.connect(App.status);
    b.event_received.connect(App.onEvent);
    b.log_message.connect(App.log);
    b.operation_progress.connect((id, p, msg) => App.log(`[op ${id}] ${p}% ${msg}`));
  }

  App.initChannel = function () {
    new QWebChannel(qt.webChannelTransport, (channel) => {
      bindBackend(channel.objects.backend);
      // Default to disconnected until backend reports otherwise
      App.status('disconnected');
    });
  };
})();
