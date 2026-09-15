"""RetailOps MCP command-line entry point.

The server implementation currently lives in the project-root ``main.py``.
Keeping this small launcher in the installable package makes the
``retailops-mcp`` console command run that server rather than the generated
placeholder that previously printed a greeting and exited.
"""

from importlib import import_module
from pathlib import Path
import sys


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    server = import_module("main")
    server.main()
