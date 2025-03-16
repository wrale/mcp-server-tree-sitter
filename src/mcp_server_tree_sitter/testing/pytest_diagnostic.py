"""Pytest plugin for enhanced diagnostic testing.

This plugin extends pytest with capabilities for detailed diagnostic reporting
while maintaining standard test pass/fail behavior.
"""

import json
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# Global storage for test context and diagnostic results
_DIAGNOSTICS = {}
_CURRENT_TEST = {}


class DiagnosticData:
    """Container for diagnostic information."""

    def __init__(self, test_id: str):
        """Initialize with test ID."""
        self.test_id = test_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = "pending"
        self.details: Dict[str, Any] = {}
        self.errors: List[Dict[str, Any]] = []
        self.artifacts: Dict[str, Any] = {}

    def add_error(self, error_type: str, message: str, tb=None):
        """Add an error to the diagnostic data."""
        error_info = {
            "type": error_type,
            "message": message,
        }
        if tb:
            error_info["traceback"] = tb
        self.errors.append(error_info)
        self.status = "error"

    def add_detail(self, key: str, value: Any):
        """Add a detail to the diagnostic data."""
        self.details[key] = value

    def add_artifact(self, name: str, content: Any):
        """Add an artifact to the diagnostic data."""
        self.artifacts[name] = content

    def finalize(self, status="completed"):
        """Mark the diagnostic as complete."""
        self.end_time = time.time()
        if not self.errors:
            self.status = status

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "test_id": self.test_id,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time if self.end_time else None,
            "details": self.details,
            "errors": self.errors,
            "artifacts": self.artifacts,
        }


@pytest.fixture
def diagnostic(request):
    """Fixture to provide diagnostic functionality to tests."""
    # Get the current test ID
    test_id = f"{request.path}::{request.node.name}"

    # Create a diagnostic data instance
    diag = DiagnosticData(test_id)
    _DIAGNOSTICS[test_id] = diag

    yield diag

    # Finalize the diagnostic when the test is done
    diag.finalize()


def pytest_configure(config):
    """Set up the plugin when pytest starts."""
    # Register additional markers
    config.addinivalue_line(
        "markers", "diagnostic: mark test as producing diagnostic information"
    )


def pytest_runtest_protocol(item, nextitem):
    """Custom test protocol that captures detailed diagnostics."""
    # Use the standard protocol
    return None


def pytest_runtest_setup(item):
    """Set up the test environment."""
    # This is no longer needed as we use the request fixture
    pass


def pytest_runtest_teardown(item):
    """Clean up after a test."""
    # This is no longer needed as we use the request fixture
    pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add diagnostic summary to the terminal output."""
    if _DIAGNOSTICS:
        terminalreporter.write_sep("=", "Diagnostic Summary")
        error_count = sum(1 for d in _DIAGNOSTICS.values() if d.status == "error")
        terminalreporter.write_line(
            f"Collected {len(_DIAGNOSTICS)} diagnostics, {error_count} with errors"
        )

        # If there are errors, show details
        if error_count:
            terminalreporter.write_sep("-", "Error Details")
            for test_id, diag in _DIAGNOSTICS.items():
                if diag.status == "error":
                    terminalreporter.write_line(f"- {test_id}")
                    for i, error in enumerate(diag.errors):
                        terminalreporter.write_line(
                            f"  Error {i+1}: {error['type']}: {error['message']}"
                        )


def pytest_sessionfinish(session, exitstatus):
    """Generate JSON reports at the end of the test session."""
    output_dir = Path("diagnostic_results")
    output_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"diagnostic_results_{timestamp}.json"

    # Convert diagnostics to JSON-serializable dict
    diagnostics_dict = {k: v.to_dict() for k, v in _DIAGNOSTICS.items()}

    # Write the results to a file
    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "diagnostics": diagnostics_dict,
                "summary": {
                    "total": len(diagnostics_dict),
                    "errors": sum(
                        1 for d in diagnostics_dict.values() if d["status"] == "error"
                    ),
                    "completed": sum(
                        1
                        for d in diagnostics_dict.values()
                        if d["status"] == "completed"
                    ),
                },
            },
            f,
            indent=2,
        )

    print(f"\nDiagnostic results saved to {output_file}")


@pytest.hookimpl(tryfirst=True)
def pytest_exception_interact(node, call, report):
    """Capture exception details for diagnostics."""
    if call.excinfo:
        try:
            test_id = f"{node.path}::{node.name}"
            if test_id in _DIAGNOSTICS:
                diag = _DIAGNOSTICS[test_id]
                exc_type = call.excinfo.type.__name__
                exc_value = str(call.excinfo.value)
                tb_str = "\n".join(traceback.format_tb(call.excinfo.tb))
                diag.add_error(exc_type, exc_value, tb_str)
        except Exception as e:
            print(f"Error recording diagnostic info: {e}")
