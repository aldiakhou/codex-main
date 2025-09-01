from __future__ import annotations

from typing import Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QFormLayout,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QPlainTextEdit, QFileDialog, QMessageBox
)

from ..core.codex_config_manager import get_codex_config_manager
from ..core.codex_settings import (
    CodexConfig,
    ModelProvider,
    McpServer,
    ShellEnvironmentPolicy,
    SandboxWorkspaceWrite,
    History,
)


class SettingsDialog(QDialog):
    """Settings dialog to manage Codex CLI/config.

    Focuses on correctness and coverage of core options. Complex nested
    structures (providers, MCP servers) are edited via simple dialogs.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(840, 640)

        self._cfg_mgr = get_codex_config_manager()
        self._cfg: CodexConfig = self._cfg_mgr.load()

        self.apply_and_restart_requested = False

        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # Tabs
        self._init_general_tab()
        self._init_safety_tab()
        self._init_shell_env_tab()
        self._init_providers_tab()
        self._init_mcp_tab()
        self._init_history_tab()
        self._init_reasoning_tab()
        self._init_advanced_tab()

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_save = QPushButton("Save")
        self.btn_apply_restart = QPushButton("Apply && Restart")
        self.btn_cancel = QPushButton("Cancel")
        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_apply_restart)
        btns.addWidget(self.btn_cancel)
        root.addLayout(btns)

        self.btn_save.clicked.connect(self._on_save)
        self.btn_apply_restart.clicked.connect(self._on_apply_and_restart)
        self.btn_cancel.clicked.connect(self.reject)

    # ---------- Tabs ----------

    def _init_general_tab(self):
        w = QWidget()
        form = QFormLayout(w)

        self.edit_model = QLineEdit(self._cfg.model or "")
        self.edit_provider = QLineEdit(self._cfg.model_provider or "")

        self.spin_ctx = QSpinBox()
        self.spin_ctx.setRange(0, 10_000_000)
        self.spin_ctx.setValue(self._cfg.model_context_window or 0)

        self.spin_max_out = QSpinBox()
        self.spin_max_out.setRange(0, 10_000_000)
        self.spin_max_out.setValue(self._cfg.model_max_output_tokens or 0)

        self.combo_verbosity = QComboBox()
        for v in ["", "low", "medium", "high"]:
            self.combo_verbosity.addItem(v)
        if self._cfg.model_verbosity:
            self.combo_verbosity.setCurrentText(self._cfg.model_verbosity)

        self.combo_file_opener = QComboBox()
        for v in ["", "vscode", "vscode-insiders", "windsurf", "cursor", "none"]:
            self.combo_file_opener.addItem(v)
        if self._cfg.file_opener:
            self.combo_file_opener.setCurrentText(self._cfg.file_opener)

        self.spin_proj_doc = QSpinBox()
        self.spin_proj_doc.setRange(0, 100_000_000)
        self.spin_proj_doc.setValue(self._cfg.project_doc_max_bytes or 0)

        self.edit_profile = QLineEdit(self._cfg.profile or "")

        form.addRow("Model", self.edit_model)
        form.addRow("Provider", self.edit_provider)
        form.addRow("Context window", self.spin_ctx)
        form.addRow("Max output tokens", self.spin_max_out)
        form.addRow("Verbosity", self.combo_verbosity)
        form.addRow("File opener", self.combo_file_opener)
        form.addRow("AGENTS.md bytes", self.spin_proj_doc)
        form.addRow("Active profile", self.edit_profile)

        self.tabs.addTab(w, "General")

    def _init_safety_tab(self):
        w = QWidget()
        form = QFormLayout(w)

        self.combo_approval = QComboBox()
        for v in ["", "untrusted", "on-failure", "on-request", "never"]:
            self.combo_approval.addItem(v)
        if self._cfg.approval_policy:
            self.combo_approval.setCurrentText(self._cfg.approval_policy)

        self.combo_sandbox = QComboBox()
        for v in ["", "read-only", "workspace-write", "danger-full-access"]:
            self.combo_sandbox.addItem(v)
        if self._cfg.sandbox_mode:
            self.combo_sandbox.setCurrentText(self._cfg.sandbox_mode)

        # Workspace-write advanced
        sw = self._cfg.sandbox_workspace_write or SandboxWorkspaceWrite()
        self.edit_ww_roots = QPlainTextEdit("\n".join(sw.writable_roots))
        self.chk_ww_net = QCheckBox("Allow network in workspace-write")
        self.chk_ww_net.setChecked(sw.network_access)
        self.chk_ww_tmpdir = QCheckBox("Exclude $TMPDIR from writable roots")
        self.chk_ww_tmpdir.setChecked(sw.exclude_tmpdir_env_var)
        self.chk_ww_slash_tmp = QCheckBox("Exclude /tmp from writable roots")
        self.chk_ww_slash_tmp.setChecked(sw.exclude_slash_tmp)

        form.addRow("Approval policy", self.combo_approval)
        form.addRow("Sandbox mode", self.combo_sandbox)
        form.addRow(QLabel("Workspace-write: writable roots (one per line)"))
        form.addRow(self.edit_ww_roots)
        form.addRow(self.chk_ww_net)
        form.addRow(self.chk_ww_tmpdir)
        form.addRow(self.chk_ww_slash_tmp)

        self.tabs.addTab(w, "Safety")

    def _init_shell_env_tab(self):
        w = QWidget()
        form = QFormLayout(w)
        sep = self._cfg.shell_environment_policy or ShellEnvironmentPolicy()

        self.combo_inherit = QComboBox()
        for v in ["all", "core", "none"]:
            self.combo_inherit.addItem(v)
        self.combo_inherit.setCurrentText(sep.inherit)

        self.chk_ignore_ex = QCheckBox("Ignore default excludes (KEY/SECRET/TOKEN)")
        self.chk_ignore_ex.setChecked(sep.ignore_default_excludes)

        self.edit_exclude = QPlainTextEdit("\n".join(sep.exclude))
        self.edit_include_only = QPlainTextEdit("\n".join(sep.include_only))

        # key=value per line
        set_lines = [f"{k}={v}" for k, v in (sep.set or {}).items()]
        self.edit_set = QPlainTextEdit("\n".join(set_lines))

        form.addRow("Inherit", self.combo_inherit)
        form.addRow(self.chk_ignore_ex)
        form.addRow(QLabel("Exclude globs (one per line)"))
        form.addRow(self.edit_exclude)
        form.addRow(QLabel("Include-only globs (one per line)"))
        form.addRow(self.edit_include_only)
        form.addRow(QLabel("Set environment (key=value per line)"))
        form.addRow(self.edit_set)

        self.tabs.addTab(w, "Shell Env")

    def _init_providers_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.list_providers = QListWidget()
        layout.addWidget(self.list_providers)
        btns = QHBoxLayout()
        self.btn_add_provider = QPushButton("Add")
        self.btn_edit_provider = QPushButton("Edit")
        self.btn_remove_provider = QPushButton("Remove")
        btns.addWidget(self.btn_add_provider)
        btns.addWidget(self.btn_edit_provider)
        btns.addWidget(self.btn_remove_provider)
        layout.addLayout(btns)

        self._refresh_providers_list()

        self.btn_add_provider.clicked.connect(self._on_add_provider)
        self.btn_edit_provider.clicked.connect(self._on_edit_provider)
        self.btn_remove_provider.clicked.connect(self._on_remove_provider)

        self.tabs.addTab(w, "Providers")

    def _init_mcp_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.list_mcp = QListWidget()
        layout.addWidget(self.list_mcp)
        btns = QHBoxLayout()
        self.btn_add_mcp = QPushButton("Add")
        self.btn_edit_mcp = QPushButton("Edit")
        self.btn_remove_mcp = QPushButton("Remove")
        btns.addWidget(self.btn_add_mcp)
        btns.addWidget(self.btn_edit_mcp)
        btns.addWidget(self.btn_remove_mcp)
        layout.addLayout(btns)

        self._refresh_mcp_list()

        self.btn_add_mcp.clicked.connect(self._on_add_mcp)
        self.btn_edit_mcp.clicked.connect(self._on_edit_mcp)
        self.btn_remove_mcp.clicked.connect(self._on_remove_mcp)

        self.tabs.addTab(w, "MCP Servers")

    def _init_history_tab(self):
        w = QWidget()
        form = QFormLayout(w)

        self.combo_hist = QComboBox()
        for v in ["save-all", "none"]:
            self.combo_hist.addItem(v)
        if self._cfg.history:
            self.combo_hist.setCurrentText(self._cfg.history.persistence)
        else:
            self.combo_hist.setCurrentText("save-all")

        self.edit_notify = QPlainTextEdit()
        if self._cfg.notify:
            self.edit_notify.setPlainText("\n".join(self._cfg.notify))

        form.addRow("History persistence", self.combo_hist)
        form.addRow(QLabel("Notify command (argv, one token per line)"))
        form.addRow(self.edit_notify)

        self.tabs.addTab(w, "History & Notify")

    def _init_reasoning_tab(self):
        w = QWidget()
        form = QFormLayout(w)

        self.chk_hide_reason = QCheckBox("Hide agent reasoning events")
        self.chk_hide_reason.setChecked(bool(self._cfg.hide_agent_reasoning))

        self.chk_show_raw = QCheckBox("Show raw agent reasoning when available")
        self.chk_show_raw.setChecked(bool(self._cfg.show_raw_agent_reasoning))

        self.combo_effort = QComboBox()
        for v in ["", "minimal", "low", "medium", "high"]:
            self.combo_effort.addItem(v)
        if self._cfg.model_reasoning_effort:
            self.combo_effort.setCurrentText(self._cfg.model_reasoning_effort)

        self.combo_summary = QComboBox()
        for v in ["", "auto", "concise", "detailed", "none"]:
            self.combo_summary.addItem(v)
        if self._cfg.model_reasoning_summary:
            self.combo_summary.setCurrentText(self._cfg.model_reasoning_summary)

        form.addRow(self.chk_hide_reason)
        form.addRow(self.chk_show_raw)
        form.addRow("Effort", self.combo_effort)
        form.addRow("Summary", self.combo_summary)

        self.tabs.addTab(w, "Reasoning")

    def _init_advanced_tab(self):
        w = QWidget()
        form = QFormLayout(w)

        self.chk_zdr = QCheckBox("Disable response storage (ZDR orgs)")
        self.chk_zdr.setChecked(bool(self._cfg.disable_response_storage))

        self.edit_instr_file = QLineEdit(self._cfg.experimental_instructions_file or "")
        self.btn_browse_instr = QPushButton("Browse…")
        self.btn_browse_instr.clicked.connect(lambda: self._browse_file(self.edit_instr_file))

        self.edit_originator = QLineEdit(self._cfg.responses_originator_header_internal_override or "")
        self.edit_chatgpt_base = QLineEdit(self._cfg.chatgpt_base_url or "")

        form.addRow(self.chk_zdr)
        row = QHBoxLayout()
        row.addWidget(self.edit_instr_file)
        row.addWidget(self.btn_browse_instr)
        form.addRow("Instructions file", row)
        form.addRow("Originator override", self.edit_originator)
        form.addRow("ChatGPT base URL", self.edit_chatgpt_base)

        self.tabs.addTab(w, "Advanced")

    # ---------- Providers CRUD ----------

    def _refresh_providers_list(self):
        self.list_providers.clear()
        for pid in sorted(self._cfg.model_providers.keys()):
            self.list_providers.addItem(QListWidgetItem(pid))

    def _on_add_provider(self):
        pid, prov = self._edit_provider_dialog()
        if pid:
            self._cfg.model_providers[pid] = prov
            self._refresh_providers_list()

    def _on_edit_provider(self):
        item = self.list_providers.currentItem()
        if not item:
            return
        pid = item.text()
        prov = self._cfg.model_providers.get(pid)
        new_pid, new_prov = self._edit_provider_dialog(pid, prov)
        if new_pid:
            # if id changed
            if new_pid != pid:
                self._cfg.model_providers.pop(pid, None)
            self._cfg.model_providers[new_pid] = new_prov
            self._refresh_providers_list()

    def _on_remove_provider(self):
        item = self.list_providers.currentItem()
        if not item:
            return
        pid = item.text()
        self._cfg.model_providers.pop(pid, None)
        self._refresh_providers_list()

    def _edit_provider_dialog(self, pid: str = "", prov: ModelProvider | None = None):
        dlg = QDialog(self)
        dlg.setWindowTitle("Model Provider")
        lay = QFormLayout(dlg)
        edit_id = QLineEdit(pid)
        edit_name = QLineEdit((prov.name if prov else "") or "")
        edit_base = QLineEdit((prov.base_url if prov else "") or "")
        edit_env = QLineEdit((prov.env_key if prov else "") or "")
        combo_wire = QComboBox()
        for v in ["", "chat", "responses"]:
            combo_wire.addItem(v)
        if prov and prov.wire_api:
            combo_wire.setCurrentText(prov.wire_api)
        edit_qp = QPlainTextEdit(self._dict_to_lines(prov.query_params if prov else {}))
        edit_hdr = QPlainTextEdit(self._dict_to_lines(prov.http_headers if prov else {}))
        edit_envhdr = QPlainTextEdit(self._dict_to_lines(prov.env_http_headers if prov else {}))

        lay.addRow("ID", edit_id)
        lay.addRow("Name", edit_name)
        lay.addRow("Base URL", edit_base)
        lay.addRow("Env key", edit_env)
        lay.addRow("Wire API", combo_wire)
        lay.addRow(QLabel("Query params (key=value per line)"))
        lay.addRow(edit_qp)
        lay.addRow(QLabel("HTTP headers (key=value per line)"))
        lay.addRow(edit_hdr)
        lay.addRow(QLabel("Env HTTP headers (header=ENV_VAR per line)"))
        lay.addRow(edit_envhdr)

        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        lay.addRow(btns)

        btn_ok.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        if dlg.exec() != QDialog.Accepted:
            return "", ModelProvider()

        out = ModelProvider(
            name=edit_name.text() or None,
            base_url=edit_base.text() or None,
            env_key=edit_env.text() or None,
            wire_api=combo_wire.currentText() or None,
            query_params=self._lines_to_dict(edit_qp.toPlainText()),
            http_headers=self._lines_to_dict(edit_hdr.toPlainText()),
            env_http_headers=self._lines_to_dict(edit_envhdr.toPlainText()),
        )
        return edit_id.text().strip(), out

    # ---------- MCP CRUD ----------

    def _refresh_mcp_list(self):
        self.list_mcp.clear()
        for sid in sorted(self._cfg.mcp_servers.keys()):
            self.list_mcp.addItem(QListWidgetItem(sid))

    def _on_add_mcp(self):
        sid, server = self._edit_mcp_dialog()
        if sid:
            self._cfg.mcp_servers[sid] = server
            self._refresh_mcp_list()

    def _on_edit_mcp(self):
        item = self.list_mcp.currentItem()
        if not item:
            return
        sid = item.text()
        server = self._cfg.mcp_servers.get(sid)
        new_sid, new_server = self._edit_mcp_dialog(sid, server)
        if new_sid:
            if new_sid != sid:
                self._cfg.mcp_servers.pop(sid, None)
            self._cfg.mcp_servers[new_sid] = new_server
            self._refresh_mcp_list()

    def _on_remove_mcp(self):
        item = self.list_mcp.currentItem()
        if not item:
            return
        sid = item.text()
        self._cfg.mcp_servers.pop(sid, None)
        self._refresh_mcp_list()

    def _edit_mcp_dialog(self, sid: str = "", server: McpServer | None = None):
        dlg = QDialog(self)
        dlg.setWindowTitle("MCP Server")
        lay = QFormLayout(dlg)
        edit_id = QLineEdit(sid)
        edit_cmd = QLineEdit((server.command if server else "") if server else "")
        edit_args = QPlainTextEdit("\n".join((server.args if server else []) or []))
        edit_env = QPlainTextEdit(self._dict_to_lines(server.env if server else {}))

        lay.addRow("ID", edit_id)
        lay.addRow("Command", edit_cmd)
        lay.addRow(QLabel("Args (one per line)"))
        lay.addRow(edit_args)
        lay.addRow(QLabel("Env (key=value per line)"))
        lay.addRow(edit_env)

        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        lay.addRow(btns)

        btn_ok.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        if dlg.exec() != QDialog.Accepted:
            return "", McpServer(command="")

        return edit_id.text().strip(), McpServer(
            command=edit_cmd.text().strip(),
            args=[a for a in edit_args.toPlainText().splitlines() if a.strip()],
            env=self._lines_to_dict(edit_env.toPlainText()),
        )

    # ---------- Actions ----------

    def _on_save(self):
        try:
            self._collect_to_model()
            self._cfg_mgr.save(self._cfg)
            QMessageBox.information(self, "Settings", "Saved to ~/.codex/config.toml")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", str(e))

    def _on_apply_and_restart(self):
        try:
            self._collect_to_model()
            self._cfg_mgr.save(self._cfg)
            self.apply_and_restart_requested = True
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Apply Failed", str(e))

    # ---------- Utils ----------

    def _collect_to_model(self) -> None:
        # General
        self._cfg.model = self.edit_model.text().strip() or None
        self._cfg.model_provider = self.edit_provider.text().strip() or None
        self._cfg.model_context_window = (self.spin_ctx.value() or None)
        self._cfg.model_max_output_tokens = (self.spin_max_out.value() or None)
        self._cfg.model_verbosity = self.combo_verbosity.currentText() or None
        self._cfg.file_opener = self.combo_file_opener.currentText() or None
        self._cfg.project_doc_max_bytes = (self.spin_proj_doc.value() or None)
        self._cfg.profile = self.edit_profile.text().strip() or None

        # Safety
        self._cfg.approval_policy = self.combo_approval.currentText() or None
        self._cfg.sandbox_mode = self.combo_sandbox.currentText() or None
        sw = SandboxWorkspaceWrite(
            writable_roots=[s for s in self.edit_ww_roots.toPlainText().splitlines() if s.strip()],
            network_access=self.chk_ww_net.isChecked(),
            exclude_tmpdir_env_var=self.chk_ww_tmpdir.isChecked(),
            exclude_slash_tmp=self.chk_ww_slash_tmp.isChecked(),
        )
        # Only set if any field is non-default
        if sw.writable_roots or sw.network_access or sw.exclude_tmpdir_env_var or sw.exclude_slash_tmp:
            self._cfg.sandbox_workspace_write = sw
        else:
            self._cfg.sandbox_workspace_write = None

        # Shell Env
        self._cfg.shell_environment_policy = ShellEnvironmentPolicy(
            inherit=self.combo_inherit.currentText() or "all",
            ignore_default_excludes=self.chk_ignore_ex.isChecked(),
            exclude=[s for s in self.edit_exclude.toPlainText().splitlines() if s.strip()],
            set=self._lines_to_dict(self.edit_set.toPlainText()),
            include_only=[s for s in self.edit_include_only.toPlainText().splitlines() if s.strip()],
        )

        # History & Notify
        self._cfg.history = History(persistence=self.combo_hist.currentText() or "save-all")
        notify_lines = [s for s in self.edit_notify.toPlainText().splitlines() if s.strip()]
        self._cfg.notify = notify_lines or None

        # Reasoning
        self._cfg.hide_agent_reasoning = self.chk_hide_reason.isChecked()
        self._cfg.show_raw_agent_reasoning = self.chk_show_raw.isChecked()
        self._cfg.model_reasoning_effort = self.combo_effort.currentText() or None
        self._cfg.model_reasoning_summary = self.combo_summary.currentText() or None

        # Advanced
        self._cfg.disable_response_storage = self.chk_zdr.isChecked()
        self._cfg.experimental_instructions_file = self.edit_instr_file.text().strip() or None
        self._cfg.responses_originator_header_internal_override = (
            self.edit_originator.text().strip() or None
        )
        self._cfg.chatgpt_base_url = self.edit_chatgpt_base.text().strip() or None

    def _dict_to_lines(self, d: Dict[str, Any]) -> str:
        return "\n".join(f"{k}={v}" for k, v in (d or {}).items())

    def _lines_to_dict(self, text: str) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
        return out

    def _browse_file(self, target: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path:
            target.setText(path)

