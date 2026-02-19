#!/usr/bin/env python3
"""SHA256-based duplicate file finder with two-pass algorithm."""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable


# Directories to skip during scanning
SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".Trash", "Library", ".cache", ".npm", ".nvm",
}

# Minimum file size to consider (1 KB)
MIN_FILE_SIZE = 1024

# Default scan paths
DEFAULT_SCAN_PATHS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
]


def _hash_file(filepath: Path, chunk_size: int = 8192) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def scan_files(
    scan_paths: Optional[List[Path]] = None,
    min_size: int = MIN_FILE_SIZE,
    max_depth: int = 8,
) -> Dict[int, List[Path]]:
    """Pass 1: Group files by size. Returns {size: [path1, path2, ...]}."""
    if scan_paths is None:
        scan_paths = DEFAULT_SCAN_PATHS

    size_groups: Dict[int, List[Path]] = {}

    def _walk(directory: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for entry in directory.iterdir():
                if entry.is_symlink():
                    continue
                if entry.is_dir():
                    if entry.name in SKIP_DIRS:
                        continue
                    _walk(entry, depth + 1)
                elif entry.is_file():
                    try:
                        size = entry.stat().st_size
                        if size >= min_size:
                            size_groups.setdefault(size, []).append(entry)
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass

    for sp in scan_paths:
        if sp.exists():
            _walk(sp, 0)

    # Keep only sizes with 2+ files (potential duplicates)
    return {s: paths for s, paths in size_groups.items() if len(paths) >= 2}


def find_duplicates(
    scan_paths: Optional[List[Path]] = None,
    min_size: int = MIN_FILE_SIZE,
    max_depth: int = 8,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[Tuple[str, int, List[Path]]]:
    """
    Two-pass duplicate finder.

    Returns list of (hash, file_size, [path1, path2, ...]) for each duplicate group.
    progress_callback(current, total) is called during hashing if provided.
    """
    # Pass 1: group by size
    size_groups = scan_files(scan_paths, min_size, max_depth)

    # Count total files to hash
    total_to_hash = sum(len(paths) for paths in size_groups.values())
    hashed = 0

    # Pass 2: hash files with same size
    hash_groups: Dict[str, Tuple[int, List[Path]]] = {}

    for size, paths in size_groups.items():
        for filepath in paths:
            try:
                file_hash = _hash_file(filepath)
                if file_hash in hash_groups:
                    hash_groups[file_hash][1].append(filepath)
                else:
                    hash_groups[file_hash] = (size, [filepath])
            except (OSError, PermissionError):
                pass
            hashed += 1
            if progress_callback:
                progress_callback(hashed, total_to_hash)

    # Return only groups with 2+ files (true duplicates)
    result = []
    for file_hash, (size, paths) in hash_groups.items():
        if len(paths) >= 2:
            result.append((file_hash, size, paths))

    # Sort by wasted space descending (size * (count - 1))
    result.sort(key=lambda x: x[1] * (len(x[2]) - 1), reverse=True)
    return result
