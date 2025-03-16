"""Project model for MCP server."""

import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..exceptions import ProjectError
from ..utils.path import get_project_root, normalize_path


class Project:
    """Represents a project for code analysis."""

    def __init__(self, name: str, path: Path, description: Optional[str] = None):
        self.name = name
        self.root_path = path
        self.description = description
        self.languages: Dict[str, int] = {}  # Language -> file count
        self.last_scan_time = 0
        self.scan_lock = threading.Lock()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "root_path": str(self.root_path),
            "description": self.description,
            "languages": self.languages,
            "last_scan_time": self.last_scan_time,
        }

    def scan_files(self, language_registry: Any, force: bool = False) -> Dict[str, int]:
        """
        Scan project files and identify languages.

        Args:
            language_registry: LanguageRegistry instance
            force: Whether to force rescan

        Returns:
            Dictionary of language -> file count
        """
        # Skip scan if it was done recently and not forced
        if not force and time.time() - self.last_scan_time < 60:  # 1 minute
            return self.languages

        with self.scan_lock:
            languages: Dict[str, int] = {}
            scanned: Set[str] = set()

            for root, _, files in os.walk(self.root_path):
                # Skip hidden directories
                if any(part.startswith(".") for part in Path(root).parts):
                    continue

                for file in files:
                    # Skip hidden files
                    if file.startswith("."):
                        continue

                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.root_path)

                    # Skip already scanned files
                    if rel_path in scanned:
                        continue

                    language = language_registry.language_for_file(file)
                    if language:
                        languages[language] = languages.get(language, 0) + 1

                    scanned.add(rel_path)

            self.languages = languages
            self.last_scan_time = int(time.time())
            return languages

    def get_file_path(self, relative_path: str) -> Path:
        """
        Get absolute file path from project-relative path.

        Args:
            relative_path: Path relative to project root

        Returns:
            Absolute Path

        Raises:
            ProjectError: If path is outside project root
        """
        # Normalize relative path to avoid directory traversal
        norm_path = normalize_path(self.root_path / relative_path)

        # Check path is inside project
        if not str(norm_path).startswith(str(self.root_path)):
            raise ProjectError(f"Path '{relative_path}' is outside project root")

        return norm_path


class ProjectRegistry:
    """Manages projects for code analysis. Implements singleton pattern."""

    # Class-level instance for singleton pattern
    _instance = None
    _class_lock = threading.RLock()

    # Instance variables - declare here for mypy
    projects: Dict[str, Project]
    _instance_lock: threading.Lock

    def __new__(cls) -> "ProjectRegistry":
        """Ensure only one instance exists."""
        with cls._class_lock:
            if cls._instance is None:
                cls._instance = super(ProjectRegistry, cls).__new__(cls)
                cls._instance.projects = {}
                cls._instance._instance_lock = threading.Lock()
            return cls._instance

    def register_project(self, name: str, path: str, description: Optional[str] = None) -> Project:
        """
        Register a new project.

        Args:
            name: Project name
            path: Project path
            description: Optional project description

        Returns:
            Registered Project

        Raises:
            ProjectError: If project already exists or path is invalid
        """
        with self._instance_lock:
            if name in self.projects:
                raise ProjectError(f"Project '{name}' already exists")

            try:
                norm_path = normalize_path(path, ensure_absolute=True)
                if not norm_path.exists():
                    raise ProjectError(f"Path does not exist: {path}")
                if not norm_path.is_dir():
                    raise ProjectError(f"Path is not a directory: {path}")

                # Try to find project root
                project_root = get_project_root(norm_path)
                project = Project(name, project_root, description)
                self.projects[name] = project
                return project
            except Exception as e:
                raise ProjectError(f"Failed to register project: {e}") from e

    def get_project(self, name: str) -> Project:
        """
        Get a project by name.

        Args:
            name: Project name

        Returns:
            Project

        Raises:
            ProjectError: If project doesn't exist
        """
        with self._instance_lock:
            if name not in self.projects:
                raise ProjectError(f"Project '{name}' not found")
            return self.projects[name]

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all registered projects.

        Returns:
            List of project dictionaries
        """
        with self._instance_lock:
            return [project.to_dict() for project in self.projects.values()]

    def remove_project(self, name: str) -> None:
        """
        Remove a project.

        Args:
            name: Project name

        Raises:
            ProjectError: If project doesn't exist
        """
        with self._instance_lock:
            if name not in self.projects:
                raise ProjectError(f"Project '{name}' not found")
            del self.projects[name]
