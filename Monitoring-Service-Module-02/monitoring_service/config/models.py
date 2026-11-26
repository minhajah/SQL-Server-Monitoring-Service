"""Immutable local settings; central collection policy remains in SQL Server."""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepositorySettings:
    server: str
    database: str
    driver: str
    authentication: str
    credential_reference: str | None
    connection_timeout_seconds: int
    command_timeout_seconds: int


@dataclass(frozen=True)
class Settings:
    repository: RepositorySettings
    maximum_concurrent_connections: int
    monitoring_enabled: bool
    production_collection_enabled: bool
    pilot_mode_enabled: bool
    email_enabled: bool
    log_directory: Path
    report_directory: Path
