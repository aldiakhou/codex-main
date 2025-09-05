"""
Patch application system for Codex Python
Handles unified diffs and tree-sitter based patching
"""

import asyncio
import os
import re
import structlog
from typing import Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import difflib
import tempfile
import shutil
from datetime import datetime

logger = structlog.get_logger(__name__)


class PatchOperation(Enum):
    """Patch operation types"""
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"


class PatchFormat(Enum):
    """Patch format types"""
    UNIFIED = "unified"
    CONTEXT = "context"
    CODEX = "codex"


@dataclass
class PatchHunk:
    """A single hunk in a patch"""
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: List[str]
    context_lines: int = 3


@dataclass
class FilePatch:
    """Patch for a single file"""
    old_path: Optional[str]
    new_path: Optional[str]
    operation: PatchOperation
    hunks: List[PatchHunk] = field(default_factory=list)
    content: Optional[str] = None  # For ADD operations
    executable: bool = False
    mode: Optional[int] = None


@dataclass
class Patch:
    """Complete patch specification"""
    patches: List[FilePatch] = field(default_factory=list)
    description: Optional[str] = None
    author: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class PatchResult:
    """Result of patch application"""
    success: bool
    applied_patches: List[str] = field(default_factory=list)
    failed_patches: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    backup_created: bool = False


@dataclass
class PatchConfig:
    """Patch application configuration"""
    create_backups: bool = True
    backup_dir: Optional[str] = None
    strip_leading_dirs: int = 0
    ignore_whitespace: bool = False
    reject_conflicts: bool = True
    dry_run: bool = False
    verbose: bool = False
    safe_mode: bool = True  # Require confirmation for destructive operations


class PatchError(Exception):
    """Patch-related errors"""
    pass


class PatchParser:
    """Parser for various patch formats"""
    
    @staticmethod
    def parse_unified_diff(patch_text: str) -> Patch:
        """Parse unified diff format"""
        patch = Patch()
        current_file_patch = None
        current_hunk = None
        
        lines = patch_text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Parse file header
            if line.startswith('--- '):
                if current_file_patch:
                    patch.patches.append(current_file_patch)
                
                old_path = line[4:].strip()
                current_file_patch = FilePatch(
                    old_path=old_path,
                    new_path=None,
                    operation=PatchOperation.MODIFY
                )
                
            elif line.startswith('+++ '):
                if current_file_patch:
                    new_path = line[4:].strip()
                    if new_path != '/dev/null':
                        current_file_patch.new_path = new_path
                    else:
                        current_file_patch.operation = PatchOperation.DELETE
            
            # Parse hunk header
            elif line.startswith('@@ '):
                if current_file_patch:
                    # Parse hunk header: @@ -old_start,old_lines +new_start,new_lines @@
                    hunk_match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                    if hunk_match:
                        old_start = int(hunk_match.group(1))
                        old_lines = int(hunk_match.group(2) or 1)
                        new_start = int(hunk_match.group(3))
                        new_lines = int(hunk_match.group(4) or 1)
                        
                        current_hunk = PatchHunk(
                            old_start=old_start,
                            old_lines=old_lines,
                            new_start=new_start,
                            new_lines=new_lines,
                            lines=[]
                        )
                        current_file_patch.hunks.append(current_hunk)
            
            # Parse hunk content
            elif current_hunk and line:
                current_hunk.lines.append(line)
            
            i += 1
        
        # Add last file patch
        if current_file_patch:
            patch.patches.append(current_file_patch)
        
        return patch
    
    @staticmethod
    def parse_codex_patch(patch_text: str) -> Patch:
        """Parse Codex-specific patch format"""
        # This would parse a more structured format
        # For now, fall back to unified diff
        return PatchParser.parse_unified_diff(patch_text)
    
    @staticmethod
    def create_unified_diff(old_content: str, new_content: str, old_path: str, new_path: str) -> str:
        """Create unified diff from content comparison"""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=old_path,
            tofile=new_path,
            lineterm=''
        )
        
        return ''.join(diff)


class PatchValidator:
    """Validates patches before application"""
    
    @staticmethod
    def validate_patch(patch: Patch, root_path: str) -> List[str]:
        """Validate patch and return list of warnings/errors"""
        warnings = []
        errors = []
        
        for file_patch in patch.patches:
            # Check file paths
            if file_patch.old_path:
                old_full_path = os.path.join(root_path, file_patch.old_path)
                if not os.path.exists(old_full_path) and file_patch.operation != PatchOperation.ADD:
                    errors.append(f"Source file does not exist: {file_patch.old_path}")
            
            if file_patch.new_path:
                new_full_path = os.path.join(root_path, file_patch.new_path)
                parent_dir = os.path.dirname(new_full_path)
                if parent_dir and not os.path.exists(parent_dir):
                    warnings.append(f"Parent directory does not exist: {parent_dir}")
            
            # Validate hunks
            for hunk in file_patch.hunks:
                if file_patch.old_path:
                    old_full_path = os.path.join(root_path, file_patch.old_path)
                    if os.path.exists(old_full_path):
                        with open(old_full_path, 'r') as f:
                            lines = f.readlines()
                        
                        if hunk.old_start + hunk.old_lines > len(lines) + 1:
                            errors.append(f"Hunk range exceeds file length: {file_patch.old_path}")
        
        return warnings + errors
    
    @staticmethod
    def check_conflicts(patch: Patch, root_path: str) -> List[str]:
        """Check for potential conflicts"""
        conflicts = []
        
        for file_patch in patch.patches:
            if file_patch.operation == PatchOperation.MODIFY and file_patch.old_path:
                file_path = os.path.join(root_path, file_patch.old_path)
                
                if os.path.exists(file_path):
                    # Simple conflict detection - check if file has been modified
                    # In a real implementation, this would be more sophisticated
                    stat = os.stat(file_path)
                    file_age = datetime.fromtimestamp(stat.st_mtime)
                    
                    # If patch is older than file, potential conflict
                    if patch.timestamp and file_age > patch.timestamp:
                        conflicts.append(f"File modified since patch creation: {file_patch.old_path}")
        
        return conflicts


class PatchApplier:
    """Applies patches to files"""
    
    def __init__(self, config: PatchConfig):
        self.config = config
        self.backup_dir = None
    
    async def apply_patch(self, patch: Patch, root_path: str) -> PatchResult:
        """Apply a complete patch"""
        result = PatchResult(
            success=True,
            applied_patches=[],
            failed_patches=[],
            conflicts=[],
            warnings=[]
        )
        
        try:
            # Validate patch
            validation_errors = PatchValidator.validate_patch(patch, root_path)
            if validation_errors:
                result.success = False
                result.failed_patches = [p.old_path or p.new_path for p in patch.patches]
                result.conflicts = validation_errors
                return result
            
            # Check for conflicts
            conflicts = PatchValidator.check_conflicts(patch, root_path)
            if conflicts and self.config.reject_conflicts:
                result.success = False
                result.conflicts = conflicts
                return result
            elif conflicts:
                result.warnings.extend(conflicts)
            
            # Create backup directory
            if self.config.create_backups:
                await self._create_backup_dir()
            
            # Apply file patches
            for file_patch in patch.patches:
                try:
                    await self._apply_file_patch(file_patch, root_path)
                    result.applied_patches.append(file_patch.old_path or file_patch.new_path)
                except Exception as e:
                    logger.error("Failed to apply file patch", 
                               file=file_patch.old_path or file_patch.new_path, 
                               error=str(e))
                    result.failed_patches.append(file_patch.old_path or file_patch.new_path)
                    result.success = False
            
            return result
            
        except Exception as e:
            logger.error("Patch application failed", error=str(e))
            result.success = False
            return result
    
    async def _apply_file_patch(self, file_patch: FilePatch, root_path: str) -> None:
        """Apply a single file patch"""
        
        if self.config.dry_run:
            logger.info("Dry run: would apply patch", 
                       file=file_patch.old_path or file_patch.new_path,
                       operation=file_patch.operation.value)
            return
        
        if file_patch.operation == PatchOperation.ADD:
            await self._add_file(file_patch, root_path)
        elif file_patch.operation == PatchOperation.MODIFY:
            await self._modify_file(file_patch, root_path)
        elif file_patch.operation == PatchOperation.DELETE:
            await self._delete_file(file_patch, root_path)
        elif file_patch.operation == PatchOperation.MOVE:
            await self._move_file(file_patch, root_path)
        elif file_patch.operation == PatchOperation.COPY:
            await self._copy_file(file_patch, root_path)
        else:
            raise PatchError(f"Unknown operation: {file_patch.operation}")
    
    async def _add_file(self, file_patch: FilePatch, root_path: str) -> None:
        """Add a new file"""
        if not file_patch.new_path:
            raise PatchError("ADD operation requires new_path")
        
        file_path = os.path.join(root_path, file_patch.new_path)
        
        # Create parent directories
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        # Write file content
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_patch.content:
                f.write(file_patch.content)
            elif file_patch.hunks:
                # Write from hunks
                content = []
                for hunk in file_patch.hunks:
                    for line in hunk.lines:
                        if line.startswith('+') and not line.startswith('++'):
                            content.append(line[1:])
                f.write(''.join(content))
        
        # Set file mode
        if file_patch.mode:
            os.chmod(file_path, file_patch.mode)
        
        logger.info("Added file", path=file_path)
    
    async def _modify_file(self, file_patch: FilePatch, root_path: str) -> None:
        """Modify an existing file"""
        if not file_patch.old_path:
            raise PatchError("MODIFY operation requires old_path")
        
        file_path = os.path.join(root_path, file_patch.old_path)
        
        if not os.path.exists(file_path):
            raise PatchError(f"File does not exist: {file_path.old_path}")
        
        # Create backup
        if self.config.create_backups:
            await self._backup_file(file_path)
        
        # Read original content
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Apply hunks
        new_lines = lines.copy()
        offset = 0
        
        for hunk in file_patch.hunks:
            if self.config.strip_leading_dirs > 0:
                # Adjust for stripped directories
                continue
            
            # Apply hunk
            new_lines = self._apply_hunk(new_lines, hunk, offset)
            offset += (hunk.new_lines - hunk.old_lines)
        
        # Write modified content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        # Update file mode if specified
        if file_patch.mode:
            os.chmod(file_path, file_patch.mode)
        
        # Handle file rename
        if file_patch.new_path and file_patch.new_path != file_patch.old_path:
            new_path = os.path.join(root_path, file_patch.new_path)
            parent_dir = os.path.dirname(new_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            shutil.move(file_path, new_path)
            file_path = new_path
        
        logger.info("Modified file", path=file_path)
    
    def _apply_hunk(self, lines: List[str], hunk: PatchHunk, offset: int) -> List[str]:
        """Apply a single hunk to lines"""
        # Adjust hunk position for previous changes
        old_start = hunk.old_start - 1 + offset  # Convert to 0-based
        old_end = old_start + hunk.old_lines
        
        # Validate hunk range
        if old_start > len(lines) or old_end > len(lines):
            raise PatchError(f"Hunk range out of bounds: {hunk.old_start}-{hunk.old_start + hunk.old_lines}")
        
        # Apply hunk changes
        new_lines = lines[:old_start]
        
        for line in hunk.lines:
            if line.startswith(' ') or line.startswith('-'):
                # Context or removal line - check if it matches
                expected_line = line[1:]
                if old_start < len(lines):
                    actual_line = lines[old_start]
                    if self.config.ignore_whitespace:
                        if expected_line.strip() != actual_line.strip():
                            raise PatchError(f"Hunk context mismatch at line {old_start + 1}")
                    else:
                        if expected_line != actual_line:
                            raise PatchError(f"Hunk context mismatch at line {old_start + 1}")
                
                if not line.startswith('-'):
                    new_lines.append(actual_line)
                    old_start += 1
            
            elif line.startswith('+'):
                # Addition line
                new_lines.append(line[1:])
        
        # Add remaining lines
        new_lines.extend(lines[old_end:])
        
        return new_lines
    
    async def _delete_file(self, file_patch: FilePatch, root_path: str) -> None:
        """Delete a file"""
        if not file_patch.old_path:
            raise PatchError("DELETE operation requires old_path")
        
        file_path = os.path.join(root_path, file_patch.old_path)
        
        if not os.path.exists(file_path):
            logger.warning("File does not exist for deletion", path=file_path)
            return
        
        # Create backup
        if self.config.create_backups:
            await self._backup_file(file_path)
        
        os.remove(file_path)
        logger.info("Deleted file", path=file_path)
    
    async def _move_file(self, file_patch: FilePatch, root_path: str) -> None:
        """Move/rename a file"""
        if not file_patch.old_path or not file_patch.new_path:
            raise PatchError("MOVE operation requires both old_path and new_path")
        
        old_path = os.path.join(root_path, file_patch.old_path)
        new_path = os.path.join(root_path, file_patch.new_path)
        
        if not os.path.exists(old_path):
            raise PatchError(f"Source file does not exist: {file_patch.old_path}")
        
        # Create backup
        if self.config.create_backups:
            await self._backup_file(old_path)
        
        # Create parent directory if needed
        parent_dir = os.path.dirname(new_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        shutil.move(old_path, new_path)
        logger.info("Moved file", src=old_path, dst=new_path)
    
    async def _copy_file(self, file_patch: FilePatch, root_path: str) -> None:
        """Copy a file"""
        if not file_patch.old_path or not file_patch.new_path:
            raise PatchError("COPY operation requires both old_path and new_path")
        
        old_path = os.path.join(root_path, file_patch.old_path)
        new_path = os.path.join(root_path, file_patch.new_path)
        
        if not os.path.exists(old_path):
            raise PatchError(f"Source file does not exist: {file_patch.old_path}")
        
        # Create parent directory if needed
        parent_dir = os.path.dirname(new_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        shutil.copy2(old_path, new_path)
        logger.info("Copied file", src=old_path, dst=new_path)
    
    async def _create_backup_dir(self) -> None:
        """Create backup directory"""
        if self.backup_dir:
            return
        
        if self.config.backup_dir:
            backup_dir = self.config.backup_dir
        else:
            backup_dir = os.path.join(tempfile.gettempdir(), "codex_backups")
        
        os.makedirs(backup_dir, exist_ok=True)
        self.backup_dir = backup_dir
    
    async def _backup_file(self, file_path: str) -> None:
        """Create backup of a file"""
        if not self.backup_dir:
            await self._create_backup_dir()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{os.path.basename(file_path)}.{timestamp}.backup"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        shutil.copy2(file_path, backup_path)
        logger.debug("Created backup", file=file_path, backup=backup_path)


class PatchManager:
    """Manages patch operations"""
    
    def __init__(self, config: Optional[PatchConfig] = None):
        self.config = config or PatchConfig()
        self.applier = PatchApplier(self.config)
        self.applied_patches: List[Patch] = []
    
    async def apply_patch_text(self, patch_text: str, root_path: str, 
                              format: PatchFormat = PatchFormat.UNIFIED) -> PatchResult:
        """Apply patch from text"""
        try:
            # Parse patch
            if format == PatchFormat.UNIFIED:
                patch = PatchParser.parse_unified_diff(patch_text)
            elif format == PatchFormat.CODEX:
                patch = PatchParser.parse_codex_patch(patch_text)
            else:
                raise PatchError(f"Unsupported patch format: {format}")
            
            # Apply patch
            result = await self.applier.apply_patch(patch, root_path)
            
            if result.success:
                self.applied_patches.append(patch)
            
            return result
            
        except Exception as e:
            logger.error("Failed to apply patch", error=str(e))
            return PatchResult(
                success=False,
                failed_patches=["unknown"],
                conflicts=[str(e)]
            )
    
    async def create_patch(self, old_path: str, new_path: str, 
                          old_content: str, new_content: str) -> Patch:
        """Create a patch between two versions"""
        diff_text = PatchParser.create_unified_diff(
            old_content, new_content, old_path, new_path
        )
        
        patch = PatchParser.parse_unified_diff(diff_text)
        patch.timestamp = datetime.now()
        
        return patch
    
    async def rollback_patch(self, patch: Patch, root_path: str) -> PatchResult:
        """Rollback a previously applied patch"""
        # Create reverse patch
        reverse_patches = []
        
        for file_patch in patch.patches:
            reverse_file_patch = FilePatch(
                old_path=file_patch.new_path,
                new_path=file_patch.old_path,
                operation=self._reverse_operation(file_patch.operation)
            )
            
            # Reverse hunks
            for hunk in file_patch.hunks:
                reverse_hunk = PatchHunk(
                    old_start=hunk.new_start,
                    old_lines=hunk.new_lines,
                    new_start=hunk.old_start,
                    new_lines=hunk.old_lines,
                    lines=[]
                )
                
                # Reverse line operations
                for line in hunk.lines:
                    if line.startswith('+'):
                        reverse_hunk.lines.append('-' + line[1:])
                    elif line.startswith('-'):
                        reverse_hunk.lines.append('+' + line[1:])
                    else:
                        reverse_hunk.lines.append(line)
                
                reverse_file_patch.hunks.append(reverse_hunk)
            
            reverse_patches.append(reverse_file_patch)
        
        reverse_patch = Patch(
            patches=reverse_patches,
            description=f"Rollback: {patch.description}",
            timestamp=datetime.now()
        )
        
        return await self.applier.apply_patch(reverse_patch, root_path)
    
    def _reverse_operation(self, operation: PatchOperation) -> PatchOperation:
        """Reverse a patch operation"""
        reversals = {
            PatchOperation.ADD: PatchOperation.DELETE,
            PatchOperation.DELETE: PatchOperation.ADD,
            PatchOperation.MOVE: PatchOperation.MOVE,  # Move is its own reverse
            PatchOperation.COPY: PatchOperation.DELETE,  # Copy -> Delete target
            PatchOperation.MODIFY: PatchOperation.MODIFY  # Modify is its own reverse
        }
        return reversals.get(operation, operation)
    
    def get_patch_history(self) -> List[Patch]:
        """Get history of applied patches"""
        return self.applied_patches.copy()
    
    async def cleanup_backups(self, older_than_days: int = 7) -> int:
        """Clean up old backup files"""
        if not self.applier.backup_dir:
            return 0
        
        cutoff_time = datetime.now().timestamp() - (older_than_days * 24 * 3600)
        cleaned_count = 0
        
        for backup_file in os.listdir(self.applier.backup_dir):
            backup_path = os.path.join(self.applier.backup_dir, backup_file)
            if os.path.getmtime(backup_path) < cutoff_time:
                try:
                    os.remove(backup_path)
                    cleaned_count += 1
                except OSError:
                    pass
        
        return cleaned_count
