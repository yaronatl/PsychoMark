"""Exercise the Codespaces start hook and live reload without a GitHub account."""

import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time

import httpx
from playwright.sync_api import Error as PlaywrightError, expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def wait_for_reload(page):
    # Plain DevTools evaluation works with our strict CSP; wait_for_function's
    # injected string predicate would require unsafe-eval on some browser versions.
    for _ in range(150):
        try:
            if page.evaluate("window.reloadProbe") is None:
                return
        except PlaywrightError:
            pass  # The execution context can disappear during the navigation.
        time.sleep(0.1)
    raise AssertionError("Browser did not reload after the source change")


def main():
    css = ROOT / "src/psychomark/static/_codespaces_test_probe.css"
    python = ROOT / "src/psychomark/_codespaces_test_probe.py"
    assert not css.exists() and not python.exists(), "Refusing to overwrite existing source files"
    css.write_text("/* initial test revision */\n")
    python.write_text("VALUE = 0\n")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    pidfile = ROOT / "artifacts/codespaces" / f"server-{port}.pid"
    logfile = ROOT / "artifacts/codespaces" / f"server-{port}.log"
    try:
        with tempfile.TemporaryDirectory(prefix="psychomark-codespaces-") as temporary:
            command = [sys.executable, str(ROOT / ".devcontainer/start.py"), "--port", str(port), "--data-dir", temporary]
            subprocess.run(command, cwd=ROOT, check=True, timeout=45)
            first_pid = pidfile.read_text()
            subprocess.run(command, cwd=ROOT, check=True, timeout=10)
            assert pidfile.read_text() == first_pid, "Start hook launched a duplicate server"
            base = f"http://127.0.0.1:{port}"
            exam = httpx.post(base + "/api/exams", json={"name": "Retained on reload", "template_id": "demo_eight_sections_v1",
                "sections": {"1": [1]}, "answer_key": {"1": {"1": 2}}}).json()
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=shutil.which("chromium") or None, headless=True)
                page = browser.new_page()
                with page.expect_response("**/api/dev/revision"):
                    page.goto(base)
                expect(page.get_by_role("heading", name="Mes examens", exact=True)).to_be_visible()
                page.evaluate("window.reloadProbe = 'before-change'")
                css.write_text("/* modified CSS revision */\n")
                wait_for_reload(page)
                expect(page.get_by_role("heading", name="Mes examens", exact=True)).to_be_visible()
                page.get_by_role("link", name="＋ Créer un examen").click()
                page.get_by_label("Nom de l’examen").fill("Conserver ma saisie")
                page.evaluate("window.reloadProbe = 'unsaved'")
                css.write_text("/* another CSS revision */\n")
                expect(page.locator(".dev-update")).to_be_visible(timeout=10000)
                expect(page.get_by_label("Nom de l’examen")).to_have_value("Conserver ma saisie")
                assert page.evaluate("window.reloadProbe") == "unsaved"
                page.get_by_role("link", name="Annuler", exact=True).click()
                wait_for_reload(page)
                browser.close()
            before = logfile.read_text().count("Started server process")
            python.write_text("VALUE = 1\n")
            for _ in range(100):
                if logfile.read_text().count("Started server process") > before:
                    try:
                        if httpx.get(base + "/api/health", timeout=1).status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                time.sleep(0.2)
            else:
                raise AssertionError("Python change did not restart the server")
            assert httpx.get(base + f"/api/exams/{exam['id']}").json()["exam"]["name"] == "Retained on reload"
            print("Codespaces hooks passed: idempotent start, browser refresh, unsaved form protection, Python restart, database retained.")
    finally:
        if pidfile.exists():
            try:
                os.killpg(int(pidfile.read_text()), signal.SIGTERM)
            except ProcessLookupError:
                pass
        css.unlink(missing_ok=True)
        python.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
