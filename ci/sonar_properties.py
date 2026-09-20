"""Añade identidad al properties sin interpolar variables en comandos shell."""
import os
from pathlib import Path


def escape(value):
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")


if __name__ == "__main__":
    if not Path("coverage.xml").is_file():
        raise SystemExit("Falta coverage.xml de esta ejecución y revisión.")
    with Path("sonar-project.properties").open("a") as output:
        for key, variable in [
            ("sonar.projectKey", "SONAR_PROJECT_KEY"),
            ("sonar.organization", "SONAR_ORGANIZATION"),
        ]:
            if value := os.environ.get(variable):
                output.write(f"\n{key}={escape(value)}\n")
