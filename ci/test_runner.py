"""El runner debe impedir que una suite vacía dé una CI exitosa."""
from unittest import TestCase, TestSuite
from unittest.mock import patch

from xmlrunner.extra.djangotestrunner import XMLTestRunner

from ci.runner import NonEmptyXMLRunner


class NonEmptyXMLRunnerTests(TestCase):
    def test_empty_suite_is_rejected(self):
        with patch.object(XMLTestRunner, "build_suite", return_value=TestSuite()):
            with self.assertRaisesRegex(RuntimeError, "Suite vacía"):
                NonEmptyXMLRunner(verbosity=0).build_suite()

    def test_nonempty_suite_is_preserved(self):
        suite = TestSuite([TestCase()])
        with patch.object(XMLTestRunner, "build_suite", return_value=suite):
            self.assertIs(NonEmptyXMLRunner(verbosity=0).build_suite(), suite)
