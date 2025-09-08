# Nexus AI Desktop

A beautiful desktop application built with Electron Forge, React, and TypeScript, featuring a modern dark theme and AI workspace interface.

## Features

- 🎨 Modern dark theme with JetBrains Mono font
- 🏢 Multiple workspaces: Dashboard, AI Agents, Code, Files, Planner, Terminal, Tools
- 🤖 AI Agent management interface with task tracking
- 💻 Built-in code editor with diff view
- 📁 File explorer and preview
- 📋 Kanban-style task planner
- 🖥️ Terminal emulator
- 🔧 MCP (Model Context Protocol) server management
- 💬 AI chat interface

## Development

### Prerequisites

- Node.js (v16 or higher)
- npm

### Installation

```bash
npm install
```

### Running the Application

```bash
npm run start
```

### Building the Application

```bash
npm run package
```

### Making Distributables

```bash
npm run make
```

## Project Structure

```
src/
├── main.ts          # Electron main process
├── preload.ts       # Preload script
└── renderer/        # React renderer process
    ├── main.tsx     # React entry point
    ├── App.tsx      # Main application component
    └── index.css    # Styles with Tailwind CSS
```

## Technologies Used

- **Electron Forge** - Build toolchain for Electron apps
- **React** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **JetBrains Mono** - Monospace font for code

## Workspaces

### Dashboard
Welcome screen with productivity overview.

### AI Agents
Manage your AI workforce with task delegation and progress tracking.

### Code
Built-in code editor with syntax highlighting and diff view.

### Files
File explorer with preview capabilities.

### Planner
Kanban-style task management board.

### Terminal
Integrated terminal for command line operations.

### Tools
Manage Model Context Protocol (MCP) servers and AI tools.

## License

MIT License
