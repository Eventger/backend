"""Comprueba el script real con archivos temporales, sin contactar Sonar."""
import os
import runpy
from contextlib import chdir
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("sonar_properties.py")


class SonarPropertiesTests(TestCase):
    def setUp(self):
        self.directory = self.enterContext(TemporaryDirectory())
        self.enterContext(chdir(self.directory))
        self.enterContext(patch.dict(os.environ, {}, clear=True))
        self.properties = Path("sonar-project.properties")
        self.original = "sonar.sources=.\n"
        self.properties.write_text(self.original)

    def run_script(self):
        runpy.run_path(str(SCRIPT), run_name="__main__")

    def test_appends_identity_preserving_configuration_without_writing_token(self):
        Path("coverage.xml").touch()
        os.environ.update(
            SONAR_PROJECT_KEY="Eventger_backend",
            SONAR_ORGANIZATION="eventger",
            SONAR_TOKEN="synthetic-token-for-test",
        )
        self.run_script()
        self.assertEqual(
            self.properties.read_text(),
            self.original
            + "\nsonar.projectKey=Eventger_backend\n"
            + "\nsonar.organization=eventger\n",
        )

    def test_escapes_backslashes_and_line_breaks_in_identity(self):
        Path("coverage.xml").touch()
        os.environ["SONAR_PROJECT_KEY"] = "project\\name\nsonar.sources=other\r"
        self.run_script()
        self.assertEqual(
            self.properties.read_text(),
            self.original + "\nsonar.projectKey=project\\\\name\\nsonar.sources=other\\r\n",
        )

    def test_missing_or_empty_identity_does_not_append_properties(self):
        Path("coverage.xml").touch()
        os.environ["SONAR_ORGANIZATION"] = ""
        self.run_script()
        self.assertEqual(self.properties.read_text(), self.original)

    def test_missing_coverage_aborts_without_modifying_configuration(self):
        with self.assertRaisesRegex(SystemExit, "Falta coverage.xml"):
            self.run_script()
        self.assertEqual(self.properties.read_text(), self.original)
