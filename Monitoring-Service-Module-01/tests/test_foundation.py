import contextlib
import io
import json
import sys
import unittest

from monitoring_service import __version__
from monitoring_service.__main__ import main


class FoundationTests(unittest.TestCase):
    def test_default_is_help_only(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([]), 0)
        self.assertIn("--check", output.getvalue())

    def test_local_check(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = main(["--check"])
        data = json.loads(output.getvalue())
        supported = sys.version_info[:2] == (3, 12)
        self.assertEqual(code, 0 if supported else 1)
        self.assertEqual(data["runtime_supported"], supported)
        self.assertFalse(data["monitoring_enabled"])
        self.assertEqual(data["database_connections_attempted"], 0)
        self.assertEqual(data["application_version"], __version__)

    def test_version(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(SystemExit) as exc:
                main(["--version"])
        self.assertEqual(exc.exception.code, 0)
        self.assertEqual(output.getvalue().strip(), __version__)

    def test_unknown_option_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as exc:
                main(["--enable-monitoring"])
        self.assertEqual(exc.exception.code, 2)
