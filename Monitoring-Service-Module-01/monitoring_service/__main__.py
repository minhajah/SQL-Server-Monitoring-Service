"""Safe command-line entry point; no database or network access."""

import argparse
import json
import sys

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(description="SQL Server Monitoring Service")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--check", action="store_true", help="Check local runtime only")
    args = parser.parse_args(argv)
    if not args.check:
        parser.print_help()
        return 0
    supported = sys.version_info[:2] == (3, 12)
    print(json.dumps({
        "application_version": __version__,
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "runtime_supported": supported,
        "monitoring_enabled": False,
        "database_connections_attempted": 0,
        "status": "READY_FOR_DEVELOPMENT" if supported else "UNSUPPORTED_RUNTIME",
    }, indent=2))
    return 0 if supported else 1


if __name__ == "__main__":
    raise SystemExit(main())
