"""Shared development commands; invoke with the project's virtualenv Python."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*arguments: str) -> None:
    print("+", " ".join(arguments), flush=True)
    subprocess.run([sys.executable, *arguments], cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "format", "test", "browser", "live", "serve"])
    command = parser.parse_args().command
    try:
        if command == "check":
            run("-m", "ruff", "check", ".")
            run("-m", "ruff", "format", "--check", ".")
            run("scripts/check_docs.py")
            run("-m", "pytest", "-q")
        elif command == "format":
            run("-m", "ruff", "check", "--select", "I", "--fix", ".")
            run("-m", "ruff", "format", ".")
        elif command == "test":
            run("-m", "pytest", "-q")
        elif command == "browser":
            run("tests/browser_smoke.py")
        elif command == "live":
            run("tests/codespaces_smoke.py")
        else:
            run("-m", "psychomark.web", "--reload", "--port", "8000")
    except subprocess.CalledProcessError as error:
        return error.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
