# Project Goal: AI Development Workbench with PySide6

Our sole objective is to build the **AI Development Workbench**, a desktop application using **Python** and the **PySide6** framework. The existing Rust TUI is deprecated and will not be used.

## Architecture

The project is composed of two primary components:

1.  **Rust Backend (`codex-rs`):** This is the core engine that provides all the powerful backend functionality, including:
    *   Agent logic for interacting with AI models.
    *   Secure, sandboxed execution of shell commands (Seatbelt on macOS, Landlock/seccomp on Linux).
    *   File system operations and patch application.
    *   A stable JSON-based protocol for integration.

2.  **PySide6 Frontend:** This is the new graphical user interface we will build from the ground up. It will act as the user-facing application and will drive the Rust backend.

**The `codex-tui` crate is considered obsolete and will be ignored entirely.**

## Backend Interaction

The PySide6 application will control the Rust backend by spawning it as a subprocess. Communication will happen over `stdin` and `stdout` using the `codex proto` command, which exposes the necessary JSON-based protocol for full functionality.

## Development Focus

All development efforts will be directed towards building the PySide6 desktop application and ensuring its seamless integration with the Rust backend.

### Backend Development Conventions

When working on the Rust backend (`codex-rs`), the existing conventions remain important:

*   **Formatting:** Use `just fmt` or `cargo fmt -- --config imports_granularity=Item`.
*   **Linting:** Use `just fix` or `cargo clippy --fix --all-features --tests`.
*   **Testing:** Run backend tests with `cargo test --all-features`.
*   **Contributions:** Follow the guidelines in `docs/contributing.md`.
