"""
File search implementation for Codex Python
High-performance fuzzy file search with filtering
"""

import asyncio
import os
import structlog
from typing import List, Dict, Set, Optional, AsyncIterator, Pattern
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re
import fnmatch
from concurrent.futures import ThreadPoolExecutor
import mimetypes

logger = structlog.get_logger(__name__)


class SearchMode(Enum):
    """Search modes"""
    FUZZY = "fuzzy"
    EXACT = "exact"
    REGEX = "regex"
    GLOB = "glob"


@dataclass
class SearchQuery:
    """Search query parameters"""
    pattern: str
    mode: SearchMode = SearchMode.FUZZY
    file_types: Optional[Set[str]] = None
    exclude_patterns: Optional[Set[str]] = None
    include_patterns: Optional[Set[str]] = None
    max_results: int = 100
    case_sensitive: bool = False
    search_content: bool = False
    path_only: bool = False
    root_path: Optional[str] = None


@dataclass
class SearchResult:
    """Search result"""
    path: str
    score: float
    type: str  # "file", "directory"
    size: Optional[int] = None
    modified_time: Optional[float] = None
    content_matches: List[Dict[str, int]] = field(default_factory=list)  # line, column matches


@dataclass
class SearchConfig:
    """Search configuration"""
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_concurrent_files: int = 50
    index_directories: bool = True
    follow_symlinks: bool = False
    respect_gitignore: bool = True
    default_exclude_patterns: Set[str] = field(default_factory=lambda: {
        "*.pyc", "*.pyo", "__pycache__", ".git", ".svn", "node_modules",
        "*.log", "*.tmp", "*.temp", ".DS_Store", "Thumbs.db"
    })
    content_search_max_size: int = 1024 * 1024  # 1MB for content search


class FuzzyMatcher:
    """Simple fuzzy matcher implementation"""
    
    def __init__(self, pattern: str, case_sensitive: bool = False):
        self.pattern = pattern.lower() if not case_sensitive else pattern
        self.case_sensitive = case_sensitive
    
    def score(self, text: str) -> float:
        """Calculate fuzzy match score (0.0 to 1.0)"""
        if not self.pattern:
            return 1.0
        
        search_text = text.lower() if not self.case_sensitive else text
        pattern = self.pattern
        
        # Exact match gets highest score
        if pattern == search_text:
            return 1.0
        
        # Startswith match
        if search_text.startswith(pattern):
            return 0.9
        
        # Contains match
        if pattern in search_text:
            # Score based on position (earlier is better)
            position = search_text.find(pattern)
            return 0.8 * (1.0 - position / len(search_text))
        
        # Character-by-character match
        pattern_chars = list(pattern)
        text_chars = list(search_text)
        pattern_idx = 0
        score = 0.0
        total_chars = len(pattern_chars)
        
        for char in text_chars:
            if pattern_idx < len(pattern_chars) and char == pattern_chars[pattern_idx]:
                score += 1.0
                pattern_idx += 1
        
        if pattern_idx == 0:
            return 0.0  # No match
        
        return score / total_chars


class FileSearcher:
    """High-performance file searcher"""
    
    def __init__(self, config: SearchConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Execute search query"""
        root_path = Path(query.root_path or os.getcwd())
        
        if not root_path.exists():
            raise ValueError(f"Root path does not exist: {root_path}")
        
        # Collect files
        files = await self._collect_files(root_path, query)
        
        # Filter and score files
        results = await self._filter_and_score_files(files, query)
        
        # Sort by score and limit results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:query.max_results]
    
    async def _collect_files(self, root_path: Path, query: SearchQuery) -> List[Path]:
        """Collect files to search"""
        files = []
        
        # Get exclude patterns
        exclude_patterns = set(self.config.default_exclude_patterns)
        if query.exclude_patterns:
            exclude_patterns.update(query.exclude_patterns)
        
        # Get include patterns
        include_patterns = query.include_patterns or set()
        
        # Walk directory tree
        for item in root_path.rglob("*"):
            try:
                # Skip if excluded
                if self._is_excluded(item, exclude_patterns):
                    continue
                
                # Check if matches include patterns
                if include_patterns and not self._matches_include_patterns(item, include_patterns):
                    continue
                
                # Handle symlinks
                if item.is_symlink():
                    if not self.config.follow_symlinks:
                        continue
                    item = item.resolve()
                
                # Collect file or directory
                if item.is_file() or (self.config.index_directories and item.is_dir()):
                    files.append(item)
                
            except (PermissionError, OSError) as e:
                logger.debug("Skipping file due to permission error", path=item, error=str(e))
                continue
        
        return files
    
    def _is_excluded(self, path: Path, exclude_patterns: Set[str]) -> bool:
        """Check if path matches exclude patterns"""
        path_str = str(path)
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True
        
        # Check gitignore if enabled
        if self.config.respect_gitignore:
            return self._check_gitignore(path)
        
        return False
    
    def _matches_include_patterns(self, path: Path, include_patterns: Set[str]) -> bool:
        """Check if path matches include patterns"""
        path_str = str(path)
        
        for pattern in include_patterns:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True
        
        return False
    
    def _check_gitignore(self, path: Path) -> bool:
        """Check if path is ignored by gitignore"""
        # Find .gitignore file
        gitignore_path = path.parent / ".gitignore"
        if not gitignore_path.exists():
            return False
        
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                gitignore_rules = f.readlines()
            
            # Simple gitignore matching
            relative_path = str(path.relative_to(path.anchor))
            for rule in gitignore_rules:
                rule = rule.strip()
                if not rule or rule.startswith('#'):
                    continue
                
                # Convert gitignore pattern to regex
                regex = self._gitignore_to_regex(rule)
                if regex and regex.search(relative_path):
                    return True
            
        except (PermissionError, OSError, UnicodeDecodeError):
            pass
        
        return False
    
    def _gitignore_to_regex(self, pattern: str) -> Optional[Pattern]:
        """Convert gitignore pattern to regex"""
        if not pattern:
            return None
        
        # Handle gitignore special characters
        regex = pattern.replace('.', r'\.')
        regex = regex.replace('*', r'[^/]*')
        regex = regex.replace('?', r'[^/]')
        regex = regex.replace('**', r'.*')
        
        # Handle directory patterns
        if pattern.endswith('/'):
            regex += r'.*'
        
        try:
            return re.compile(regex)
        except re.error:
            return None
    
    async def _filter_and_score_files(self, files: List[Path], query: SearchQuery) -> List[SearchResult]:
        """Filter and score files based on query"""
        results = []
        
        # Process files in batches
        batch_size = self.config.max_concurrent_files
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self._process_file(file, query) for file in batch],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, SearchResult):
                    results.append(result)
        
        return results
    
    async def _process_file(self, file_path: Path, query: SearchQuery) -> Optional[SearchResult]:
        """Process a single file and return search result if it matches"""
        try:
            # Get file info
            stat = file_path.stat()
            file_size = stat.st_size
            modified_time = stat.st_mtime
            
            # Skip if too large
            if file_size > self.config.max_file_size:
                return None
            
            # Check file type filter
            if query.file_types:
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if mime_type and mime_type.split('/')[0] not in query.file_types:
                    return None
            
            # Score filename match
            filename = file_path.name
            path_str = str(file_path)
            
            if query.mode == SearchMode.FUZZY:
                matcher = FuzzyMatcher(query.pattern, query.case_sensitive)
                score = max(matcher.score(filename), matcher.score(path_str))
            elif query.mode == SearchMode.EXACT:
                search_text = path_str if query.case_sensitive else path_str.lower()
                pattern = query.pattern if query.case_sensitive else query.pattern.lower()
                score = 1.0 if pattern in search_text else 0.0
            elif query.mode == SearchMode.REGEX:
                try:
                    flags = 0 if query.case_sensitive else re.IGNORECASE
                    regex = re.compile(query.pattern, flags)
                    score = 1.0 if regex.search(path_str) else 0.0
                except re.error:
                    return None
            elif query.mode == SearchMode.GLOB:
                pattern = query.pattern if query.case_sensitive else query.pattern.lower()
                search_text = path_str if query.case_sensitive else path_str.lower()
                score = 1.0 if fnmatch.fnmatch(search_text, pattern) else 0.0
            else:
                return None
            
            # Skip if no match
            if score <= 0:
                return None
            
            # Content search if requested
            content_matches = []
            if query.search_content and file_path.is_file() and file_size <= self.config.content_search_max_size:
                content_matches = await self._search_file_content(file_path, query)
                if content_matches:
                    score += 0.2  # Boost score for content matches
            
            return SearchResult(
                path=str(file_path),
                score=score,
                type="file" if file_path.is_file() else "directory",
                size=file_size,
                modified_time=modified_time,
                content_matches=content_matches
            )
            
        except (PermissionError, OSError) as e:
            logger.debug("Error processing file", path=file_path, error=str(e))
            return None
    
    async def _search_file_content(self, file_path: Path, query: SearchQuery) -> List[Dict[str, int]]:
        """Search within file content"""
        try:
            # Skip binary files
            if file_path.suffix in ['.pyc', '.exe', '.dll', '.so', '.dylib']:
                return []
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            matches = []
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                if self._line_matches(line, query):
                    # Find column positions
                    for col in self._find_match_positions(line, query):
                        matches.append({"line": line_num, "column": col})
            
            return matches
            
        except (PermissionError, OSError, UnicodeDecodeError) as e:
            logger.debug("Error searching file content", path=file_path, error=str(e))
            return []
    
    def _line_matches(self, line: str, query: SearchQuery) -> bool:
        """Check if line matches search pattern"""
        if query.mode == SearchMode.FUZZY:
            matcher = FuzzyMatcher(query.pattern, query.case_sensitive)
            return matcher.score(line) > 0.5
        elif query.mode == SearchMode.EXACT:
            search_text = line if query.case_sensitive else line.lower()
            pattern = query.pattern if query.case_sensitive else query.pattern.lower()
            return pattern in search_text
        elif query.mode == SearchMode.REGEX:
            try:
                flags = 0 if query.case_sensitive else re.IGNORECASE
                regex = re.compile(query.pattern, flags)
                return bool(regex.search(line))
            except re.error:
                return False
        elif query.mode == SearchMode.GLOB:
            pattern = query.pattern if query.case_sensitive else query.pattern.lower()
            search_text = line if query.case_sensitive else line.lower()
            return fnmatch.fnmatch(search_text, pattern)
        
        return False
    
    def _find_match_positions(self, line: str, query: SearchQuery) -> List[int]:
        """Find column positions of matches in line"""
        positions = []
        
        if query.mode == SearchMode.EXACT:
            search_text = line if query.case_sensitive else line.lower()
            pattern = query.pattern if query.case_sensitive else query.pattern.lower()
            pos = search_text.find(pattern)
            while pos >= 0:
                positions.append(pos + 1)  # 1-based column
                pos = search_text.find(pattern, pos + 1)
        
        elif query.mode == SearchMode.REGEX:
            try:
                flags = 0 if query.case_sensitive else re.IGNORECASE
                regex = re.compile(query.pattern, flags)
                for match in regex.finditer(line):
                    positions.append(match.start() + 1)  # 1-based column
            except re.error:
                pass
        
        return positions
    
    async def search_stream(self, query: SearchQuery) -> AsyncIterator[SearchResult]:
        """Stream search results as they're found"""
        root_path = Path(query.root_path or os.getcwd())
        
        if not root_path.exists():
            raise ValueError(f"Root path does not exist: {root_path}")
        
        # Stream files and process them
        async for file_path in self._stream_files(root_path, query):
            result = await self._process_file(file_path, query)
            if result:
                yield result
    
    async def _stream_files(self, root_path: Path, query: SearchQuery) -> AsyncIterator[Path]:
        """Stream files from directory tree"""
        exclude_patterns = set(self.config.default_exclude_patterns)
        if query.exclude_patterns:
            exclude_patterns.update(query.exclude_patterns)
        
        include_patterns = query.include_patterns or set()
        
        for item in root_path.rglob("*"):
            try:
                if self._is_excluded(item, exclude_patterns):
                    continue
                
                if include_patterns and not self._matches_include_patterns(item, include_patterns):
                    continue
                
                if item.is_symlink() and not self.config.follow_symlinks:
                    continue
                
                if item.is_file() or (self.config.index_directories and item.is_dir()):
                    yield item
                
            except (PermissionError, OSError):
                continue
    
    async def close(self) -> None:
        """Clean up resources"""
        self.executor.shutdown(wait=True)


class SearchManager:
    """Manages search operations"""
    
    def __init__(self, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig()
        self.searcher = FileSearcher(self.config)
        self.active_searches: Dict[str, asyncio.Task] = {}
    
    async def search(self, query: SearchQuery, search_id: Optional[str] = None) -> List[SearchResult]:
        """Execute search"""
        try:
            results = await self.searcher.search(query)
            return results
        except Exception as e:
            logger.error("Search failed", query=query.pattern, error=str(e))
            raise
    
    async def search_stream(self, query: SearchQuery, search_id: Optional[str] = None) -> AsyncIterator[SearchResult]:
        """Stream search results"""
        try:
            async for result in self.searcher.search_stream(query):
                yield result
        except Exception as e:
            logger.error("Stream search failed", query=query.pattern, error=str(e))
            raise
    
    def cancel_search(self, search_id: str) -> bool:
        """Cancel an active search"""
        if search_id in self.active_searches:
            self.active_searches[search_id].cancel()
            del self.active_searches[search_id]
            return True
        return False
    
    async def close(self) -> None:
        """Clean up search manager"""
        # Cancel all active searches
        for task in self.active_searches.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.active_searches:
            await asyncio.gather(*self.active_searches.values(), return_exceptions=True)
        
        # Close searcher
        await self.searcher.close()


# Convenience functions
async def quick_search(pattern: str, root_path: Optional[str] = None, **kwargs) -> List[SearchResult]:
    """Quick search with default parameters"""
    query = SearchQuery(pattern=pattern, root_path=root_path, **kwargs)
    searcher = FileSearcher(SearchConfig())
    try:
        return await searcher.search(query)
    finally:
        await searcher.close()


async def find_files(pattern: str, file_types: Optional[Set[str]] = None) -> List[str]:
    """Find files matching pattern"""
    query = SearchQuery(
        pattern=pattern,
        mode=SearchMode.GLOB,
        file_types=file_types,
        path_only=True
    )
    searcher = FileSearcher(SearchConfig())
    try:
        results = await searcher.search(query)
        return [result.path for result in results]
    finally:
        await searcher.close()