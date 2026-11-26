"""Strict, offline JSON validation. Never opens connections or creates directories."""
import json
import re
from pathlib import Path
from .models import RepositorySettings, Settings


class ConfigurationError(ValueError):
    """Safe diagnostic; never contains supplied configuration values."""


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigurationError("Duplicate JSON key.")
        result[key] = value
    return result


def _keys(obj, expected, section):
    if not isinstance(obj, dict) or set(obj) != set(expected):
        raise ConfigurationError(f"Missing or unexpected keys in {section}.")


def _boolean(value, field):
    if type(value) is not bool:
        raise ConfigurationError(f"{field} must be a boolean.")
    return value


def _integer(value, low, high, field):
    if type(value) is not int or not low <= value <= high:
        raise ConfigurationError(f"{field} must be an integer between {low} and {high}.")
    return value


def _text(value, field, maximum=256):
    if (not isinstance(value, str) or not value or value != value.strip()
            or len(value) > maximum or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise ConfigurationError(f"Invalid {field}.")
    return value


def _directory(value, base, field):
    value = _text(value, field, 1024)
    p = Path(value)
    if p.is_absolute() or p.drive or p.anchor or any(x in ('..', '.') for x in p.parts) or ':' in value or '\\' in value:
        raise ConfigurationError(f"{field} must be a relative forward-slash path without traversal.")
    try:
        target = (base / p).resolve()
        if target == base or not target.is_relative_to(base):
            raise ConfigurationError(f"Invalid {field} location.")
        return target
    except (OSError, RuntimeError) as exc:
        raise ConfigurationError(f"Invalid {field} location.") from exc


def load_settings(path: str | Path) -> Settings:
    try:
        path = Path(path).resolve(strict=True)
        with path.open('rb') as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ConfigurationError("Configuration exceeds 64 KiB.")
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError, RuntimeError) as exc:
        raise ConfigurationError("Cannot read valid UTF-8 JSON configuration.") from exc
    _keys(data, ('schema_version', 'repository', 'safety', 'maximum_concurrent_connections', 'paths'), 'root')
    _integer(data['schema_version'], 1, 1, 'schema_version')
    r, s, p = data['repository'], data['safety'], data['paths']
    _keys(r, ('server', 'database', 'driver', 'authentication', 'credential_reference', 'connection_timeout_seconds', 'command_timeout_seconds'), 'repository')
    _keys(s, ('monitoring_enabled', 'production_collection_enabled', 'pilot_mode_enabled', 'email_enabled'), 'safety')
    _keys(p, ('log_directory', 'report_directory'), 'paths')
    server = _text(r['server'], 'server')
    if any(c in server for c in ';={}'):  # not an ODBC connection string
        raise ConfigurationError("Server must be an endpoint, not a connection string.")
    if r['database'] != 'DBA_Monitoring' or r['driver'] != 'ODBC Driver 18 for SQL Server':
        raise ConfigurationError("Unsupported repository database or ODBC driver.")
    auth = r['authentication']
    ref = r['credential_reference']
    if auth == 'WINDOWS':
        if ref is not None:
            raise ConfigurationError("Windows authentication must not specify a credential reference.")
    elif auth == 'SQL':
        if not isinstance(ref, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,127}', ref):
            raise ConfigurationError("SQL authentication requires a credential reference identifier.")
    else:
        raise ConfigurationError("Unsupported authentication type.")
    flags = {k: _boolean(v, k) for k, v in s.items()}
    if flags['production_collection_enabled'] and not flags['monitoring_enabled']:
        raise ConfigurationError("Production collection requires monitoring to be enabled.")
    # Module 02 is validation-only. Activation is not implemented.
    if flags['monitoring_enabled'] or flags['production_collection_enabled'] or flags['email_enabled'] or not flags['pilot_mode_enabled']:
        raise ConfigurationError("Module 02 requires monitoring and email disabled, with pilot mode enabled.")
    repository = RepositorySettings(server, r['database'], r['driver'], auth, ref,
        _integer(r['connection_timeout_seconds'], 1, 300, 'connection_timeout_seconds'),
        _integer(r['command_timeout_seconds'], 1, 600, 'command_timeout_seconds'))
    base = path.parent.resolve()
    logs = _directory(p['log_directory'], base, 'log_directory')
    reports = _directory(p['report_directory'], base, 'report_directory')
    if logs == reports or logs.is_relative_to(reports) or reports.is_relative_to(logs):
        raise ConfigurationError("Log and report directories must be separate.")
    return Settings(repository, _integer(data['maximum_concurrent_connections'], 1, 2, 'maximum_concurrent_connections'),
                    flags['monitoring_enabled'], flags['production_collection_enabled'], flags['pilot_mode_enabled'], flags['email_enabled'], logs, reports)
