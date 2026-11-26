# SQL-Server-Monitoring-Service

Lightweight centralized SQL Server monitoring service designed for offline enterprise environments. Independent of any existing inventory application.

**Status:** Modules 01–02 foundation and configuration implemented; SQL integration and deployment validation pending. Not production-ready.

## Architecture and scope

- Target: Windows Server 2022, Python 3.12, central SQL Server 2019 or later.
- Planning capacity: 25 monitored instances on a host with 4 vCPU and 16 GB RAM; capacity must be tested.
- Central repository: `DBA_Monitoring`.
- SQL source: [SQL-Server-Production-Optimization](https://github.com/minhajah/SQL-Server-Production-Optimization), Modules 26 and 30. Use a pinned, reviewed SQL snapshot for integration; do not fetch scripts at runtime.
- Offline installation and runtime; no automatic remediation; no production details or credentials in GitHub.
- Initial pilot candidates exclude COL-11, COL-12 and COL-16 until incremental collection validation passes.

## Repository structure

```text
monitoring_service/
  __init__.py
  __main__.py
  config/
    __init__.py
    models.py
    loader.py
config/
  .gitignore
  settings.example.json
tests/
  test_foundation.py
  test_config.py
requirements.txt
README.md
.gitignore       # existing GitHub file; retain
LICENSE          # existing GitHub file; retain
```

## Local development checks

From the repository root on a development workstation with Python 3.12:

```powershell
py -3.12 -m monitoring_service --version
py -3.12 -m monitoring_service --check
py -3.12 -m unittest discover -s tests -v
```

No packages need to be installed. The runtime check exits with code 1 on Python versions other than 3.12. The foundation never attempts a network or database connection. Running without arguments displays help only.

## Development roadmap

| Module | Name | Status |
|---|---|---|
| 01 | Project Foundation | Implemented; target runtime validation pending |
| 02 | Configuration Management | Implemented; target validation pending |
| 03 | Database Connectivity | Next |
| 04 | Collector Execution | Planned |
| 05 | Metric Validation | Planned |
| 06 | Repository Integration | Planned |
| 07 | Collection Scheduler | Planned |
| 08 | Concurrency Management | Planned |
| 09 | Error Handling | Planned |
| 10 | Incremental Collection | Planned |
| 11 | Application Logging | Planned |
| 12 | Health Monitoring | Planned |
| 13 | Alert Management | Planned |
| 14 | Email Notifications | Planned |
| 15 | HTML Reporting | Planned |
| 16 | Monitoring Dashboard | Planned |
| 17 | Repository Maintenance | Planned |
| 18 | Windows Service | Planned |
| 19 | Offline Deployment | Planned |
| 20 | Testing and Validation | Planned throughout development |

## Safety and validation

Monitoring remains disabled until explicit authorization and non-production testing. SQL compilation, permissions, ingestion consistency, scheduling overhead, rollback and recovery must be validated before a pilot. The application has no collector, credential resolution or database connectivity implementation. Keep the existing inventory application untouched.

## Module 02 — Configuration

```powershell
py -3.12 -m monitoring_service --validate-config config/settings.example.json
```

This command only validates JSON; it does not connect or create directories. The example endpoint is a placeholder, not a verified server. Actual settings belong in `config/settings.local.json` (ignored by Git); never store credentials in JSON. SQL authentication accepts a reference identifier only; credential resolution is not implemented. Windows authentication is the default. ODBC Driver 18 is the proposed driver and is not required for these checks.

Safety flags are locked to disabled monitoring/production/email and enabled pilot mode in Module 02. The local concurrency cap is two; future execution must also obey central repository limits and switches, with either disabled switch preventing execution. Collector intervals and assignments remain in DBA_Monitoring. Relative output paths are resolved from the settings file directory (for the example, `config/runtime/`); no directories are created. Configuration validation is independent of the runtime compatibility check. Run both checks before future execution.

Version 0.2.0 uses only the standard library. Windows/Python 3.12 target testing and SQL connectivity are pending.
