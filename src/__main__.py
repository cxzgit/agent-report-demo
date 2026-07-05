from __future__ import annotations

import argparse
import sys

from .models import ReportRequest
from .orchestrator import ReportAgentOrchestrator

__title__ = "agent-report-demo"
__version__ = "0.1.0"


def main() -> None:
    parser = argparse.ArgumentParser(prog=__title__)
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("command", nargs="?", default="start", choices=["start"], help="Command to run")
    args = parser.parse_args()

    if args.command == "start":
        start_demo()
    else:
        parser.print_help()
        sys.exit(1)


def start_demo() -> None:
    request = ReportRequest(
        country="越南",
        industry="新能源",
    )

    print("=== Agent Report Demo ===")
    print(f"country: {request.country}")
    print(f"industry: {request.industry}")
    print()

    orchestrator = ReportAgentOrchestrator()
    final_state = orchestrator.run(request)

    print("\n=== Final Report ===")
    print(final_state.final_report)


if __name__ == "__main__":
    main()