import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from monitoring_service.config import ConfigurationError, load_settings
from monitoring_service.__main__ import main

EXAMPLE = Path(__file__).resolve().parents[1] / 'config/settings.example.json'


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'settings.json'
        self.data = json.loads(EXAMPLE.read_text())

    def save(self):
        self.path.write_text(json.dumps(self.data), encoding='utf-8')

    def invalid(self):
        self.save()
        with self.assertRaises(ConfigurationError):
            load_settings(self.path)

    def test_example(self):
        s = load_settings(EXAMPLE)
        self.assertFalse(s.monitoring_enabled)
        self.assertTrue(s.pilot_mode_enabled)
        self.assertEqual(s.maximum_concurrent_connections, 2)

    def test_no_directory_creation(self):
        self.save()
        s = load_settings(self.path)
        self.assertFalse(s.log_directory.exists())
        self.assertEqual(s.log_directory, self.path.parent / 'runtime/logs')

    def test_unknown_key(self):
        self.data['repository']['password'] = 'secret'
        self.invalid()

    def test_missing_key(self):
        del self.data['paths']
        self.invalid()

    def test_duplicate_key(self):
        self.path.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaises(ConfigurationError):
            load_settings(self.path)

    def test_boolean_not_integer(self):
        self.data['maximum_concurrent_connections'] = True
        self.invalid()

    def test_concurrency_cap(self):
        self.data['maximum_concurrent_connections'] = 3
        self.invalid()

    def test_activation_rejected(self):
        for key, value in [('monitoring_enabled', True), ('production_collection_enabled', True), ('email_enabled', True), ('pilot_mode_enabled', False)]:
            with self.subTest(key=key):
                original = copy.deepcopy(self.data)
                self.data['safety'][key] = value
                self.invalid()
                self.data = original

    def test_sql_reference(self):
        self.data['repository']['authentication'] = 'SQL'
        self.invalid()
        self.data['repository']['credential_reference'] = 'monitoring-repo'
        self.save()
        self.assertEqual(load_settings(self.path).repository.credential_reference, 'monitoring-repo')

    def test_windows_reference_rejected(self):
        self.data['repository']['credential_reference'] = 'unexpected'
        self.invalid()

    def test_connection_string_rejected(self):
        self.data['repository']['server'] = 'server;PWD=secret'
        self.invalid()

    def test_timeout_bounds(self):
        self.data['repository']['command_timeout_seconds'] = 0
        self.invalid()

    def test_path_traversal(self):
        self.data['paths']['log_directory'] = '../outside'
        self.invalid()

    def test_overlapping_paths(self):
        self.data['paths']['report_directory'] = 'runtime/logs/reports'
        self.invalid()

    def test_malformed_json(self):
        self.path.write_text('{')
        with self.assertRaises(ConfigurationError):
            load_settings(self.path)

    def test_cli_valid(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['--validate-config', str(EXAMPLE)]), 0)
        self.assertEqual(json.loads(out.getvalue())['database_connections_attempted'], 0)

    def test_cli_invalid_does_not_echo_secret(self):
        self.data['repository']['password'] = 'sensitive-value'
        self.save()
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(main(['--validate-config', str(self.path)]), 2)
        self.assertNotIn('sensitive-value', err.getvalue())
