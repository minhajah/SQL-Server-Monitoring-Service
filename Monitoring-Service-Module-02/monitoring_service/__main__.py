"""Safe command-line entry point; no database or network access."""

import argparse
import json
import sys

from . import __version__
from .config import ConfigurationError, load_settings


def main(argv=None):
    parser = argparse.ArgumentParser(description="SQL Server Monitoring Service")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_mutually_exclusive_group()
    commands.add_argument("--check", action="store_true", help="Check local runtime only")
    commands.add_argument("--validate-config", metavar="PATH", help="Validate local JSON without connecting")
    args = parser.parse_args(argv)
    if args.validate_config is not None:
        try:
            load_settings(args.validate_config)
        except ConfigurationError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(json.dumps({"configuration_valid": True, "monitoring_enabled": False,
                          "database_connections_attempted": 0,
                          "status": "VALIDATION_ONLY"}, indent=2))
        return 0
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
