"""Runner Django con evidencia JUnit y rechazo explícito de suites vacías."""
from xmlrunner.extra.djangotestrunner import XMLTestRunner


class NonEmptyXMLRunner(XMLTestRunner):
    def build_suite(self, *args, **kwargs):
        suite = super().build_suite(*args, **kwargs)
        if not suite.countTestCases():
            raise RuntimeError("Suite vacía: no se puede validar el Backend sin pruebas.")
        return suite
