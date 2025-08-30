# AI Development Workbench - Updated MVP Implementation Plan

## Current Foundation (Working)

- ✅ PySide6 desktop app with basic chat interface
- ✅ JSON communication protocol with Codex CLI backend
- ✅ User authentication (ChatGPT login)
- ✅ Real-time event streaming from backend
- ✅ Process management and error handling

## Core Goal

Build a desktop application that orchestrates AI-assisted code changes across local repositories, providing a user-friendly interface for:

- Repository management and file exploration
- AI-powered code editing with diff review
- Task orchestration and workflow management
- Artifact storage and run history

---

## Phase 1: Enhanced UI & Repository Management (2-3 weeks)

### 1.1 UI Structure Enhancement

- [ ] Convert to dock-based layout (repo explorer, diff view, console, artifacts)
- [ ] Add menu bar with File, View, Tools menus
- [ ] Implement status bar with backend connection status
- [ ] Add toolbar with common actions (open repo, run task, etc.)

### 1.2 Repository Management

- [ ] Add repository selection dialog
- [ ] Implement file tree view for current repository
- [ ] Add git status integration (modified, staged, untracked files)
- [ ] Basic file operations (open, edit, save)

### 1.3 Configuration System

- [ ] Create config file support (~/.ai-workbench/config.json)
- [ ] Store repository paths, UI preferences, backend settings
- [ ] Add settings dialog for configuration

### 1.4 Enhanced Communication Protocol

- [ ] Extend JSON protocol for file operations
- [ ] Add repository context to operations
- [ ] Implement file content streaming

---

## Phase 2: Code Editing & Diff System (3-4 weeks)

### 2.1 Code Editor Integration
- [ ] Add syntax-highlighted code editor widget
- [ ] Implement file opening from repository tree
- [ ] Basic editing capabilities with save/discard
- [ ] Line numbers and basic editor features

### 2.2 Diff View Implementation
- [ ] Create side-by-side diff viewer
- [ ] Syntax highlighting for diffs
- [ ] Hunk selection and staging controls
- [ ] Apply/reject individual changes

### 2.3 AI-Assisted Editing Workflow
- [ ] Extend protocol for "edit_file" operations
- [ ] Send file context with user prompts
- [ ] Parse and display AI-generated diffs
- [ ] Implement approval workflow for changes

### 2.4 Basic Task System
- [ ] Create simple task runner for single operations
- [ ] Add progress indicators for long-running tasks
- [ ] Implement task cancellation
- [ ] Basic error handling and retry logic

---

## Phase 3: Workflow Orchestration (4-5 weeks)

### 3.1 Task Definition System
- [ ] JSON-based task templates
- [ ] Support for multi-step workflows
- [ ] Task parameters and variables
- [ ] Task chaining and dependencies

### 3.2 Workflow Editor
- [ ] Visual workflow builder (drag-and-drop)
- [ ] Task library with common operations
- [ ] Save/load workflow templates
- [ ] Workflow validation

### 3.3 Execution Engine
- [ ] Multi-step task execution
- [ ] Parallel task execution where possible
- [ ] Rollback capabilities
- [ ] Execution state persistence

### 3.4 Run History & Artifacts
- [ ] Store execution history
- [ ] Save generated artifacts (diffs, logs, reports)
- [ ] Run comparison and replay
- [ ] Export/import workflows

---

## Phase 4: Advanced Features & Polish (3-4 weeks)

### 4.1 Testing Integration
- [ ] Test discovery and execution
- [ ] Test result visualization
- [ ] Integration with popular test frameworks
- [ ] Test-driven development workflow

### 4.2 Plugin System
- [ ] Plugin architecture for extensibility
- [ ] Custom task types
- [ ] Alternative AI providers
- [ ] Custom UI components

### 4.3 Advanced Repository Features
- [ ] Branch management
- [ ] Commit/stash operations
- [ ] Conflict resolution
- [ ] Repository comparison

### 4.4 Production Polish
- [ ] Comprehensive error handling
- [ ] Logging and debugging tools
- [ ] Performance optimization
- [ ] User documentation and help system

---

## Technical Implementation Details

### JSON Protocol Extensions

Current operations:
```json
{
  "id": "unique_id",
  "op": {
    "type": "user_input",
    "items": [{"type": "text", "text": "prompt"}]
  }
}
```

Extended operations for Phase 1-2:
```json
{
  "id": "op_1",
  "op": {
    "type": "open_repository",
    "path": "/path/to/repo"
  }
}

{
  "id": "op_2", 
  "op": {
    "type": "read_file",
    "path": "src/main.py",
    "context": {"lines": 50}
  }
}

{
  "id": "op_3",
  "op": {
    "type": "edit_file",
    "path": "src/main.py", 
    "instruction": "Add error handling",
    "context": {"start_line": 10, "end_line": 20}
  }
}
```

### Data Models

```python
# aiw/core/models.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Repository(BaseModel):
    path: str
    name: str
    current_branch: str
    
class FileEdit(BaseModel):
    path: str
    original_content: str
    new_content: str
    diff: str
    
class Task(BaseModel):
    id: str
    name: str
    type: str
    parameters: dict
    status: str
    
class Workflow(BaseModel):
    id: str
    name: str
    tasks: List[Task]
    created_at: datetime
```

### UI Component Structure

```
MainWindow
├── MenuBar
├── ToolBar  
├── StatusBar
├── CentralWidget
│   ├── RepositoryDock
│   ├── EditorDock
│   ├── DiffDock
│   ├── ConsoleDock
│   └── ArtifactsDock
└── BackendService
```

### File Organization

```
ai-workbench/
├── main.py                 # Application entry point
├── requirements.txt        # Dependencies
├── aiw/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── backend_service.py  # Codex communication
│   │   ├── models.py           # Data models
│   │   ├── config.py           # Configuration management
│   │   └── task_runner.py      # Task execution engine
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py      # Main application window
│       ├── repository_dock.py  # Repository explorer
│       ├── editor_widget.py    # Code editor
│       ├── diff_view.py        # Diff viewer
│       ├── console_widget.py   # Console output
│       └── workflow_editor.py  # Visual workflow builder
```

---

## Success Metrics

### Phase 1 Success
- [ ] App starts with dock-based UI
- [ ] Can open and browse repository files
- [ ] Basic file editing works
- [ ] Settings are persisted

### Phase 2 Success  
- [ ] Can request AI edits on files
- [ ] Diff viewer shows changes clearly
- [ ] Can apply/reject individual hunks
- [ ] Basic workflows execute successfully

### Phase 3 Success
- [ ] Multi-step workflows work
- [ ] Visual workflow editor functional
- [ ] Run history and artifacts saved
- [ ] Error recovery works

### Phase 4 Success
- [ ] Testing integration complete
- [ ] Plugin system extensible
- [ ] Performance optimized
- [ ] User documentation complete

---

## Risk Mitigation

### Technical Risks
- **Codex Protocol Changes**: Maintain abstraction layer for protocol updates
- **Performance Issues**: Implement lazy loading and background processing
- **Memory Usage**: Stream large files and diffs
- **UI Responsiveness**: Use threading for long operations

### Project Risks  
- **Scope Creep**: Stick to phased approach, validate each phase
- **Dependency Issues**: Pin versions, test compatibility
- **User Adoption**: Focus on core workflows first
- **Maintenance**: Keep code clean and well-documented

---

## Next Steps

1. **Immediate (This Week)**:
   - Review and finalize this plan
   - Set up development environment
   - Create basic project structure

2. **Week 1-2**: Implement Phase 1.1-1.2 (UI enhancement + repo management)
3. **Week 3-4**: Complete Phase 1 (configuration + protocol extensions)
4. **Week 5-7**: Implement Phase 2 (editing + diff system)

This plan builds directly on your working foundation while systematically achieving the original goal of an AI-assisted code development workbench.</content>
<parameter name="filePath">c:\Users\ali95\Documents\Dev\codex-main\ai-workbench\MVP_IMPLEMENTATION_PLAN.md
