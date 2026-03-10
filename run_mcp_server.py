"""Launcher for MCP dev/run when using file-based spec (mcp dev <file>:mcp).

The MCP CLI expects a Python file path, not a module name. This script adds
src to PYTHONPATH and imports the real server so that 'mcp dev run_mcp_server.py:mcp'
and 'mcp run run_mcp_server.py:mcp' work from the repo root.
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
_src = _root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

