"""Real Chromium workflow on an isolated server/database; run separately from pytest."""

import argparse
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from browser_corpus import exercise_corpus
from browser_sheets import exercise_sheets
from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/browser"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="psychomark-browser-") as temporary:
        root = Path(temporary)
        with (root / "server.log").open("w") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "psychomark.web",
                    "--data-dir",
                    str(root / "data"),
                    "--port",
                    str(port),
                ],
                stdout=log,
                stderr=log,
            )
            try:
                base = f"http://127.0.0.1:{port}"
                for attempt in range(100):
                    if process.poll() is not None:
                        raise RuntimeError((root / "server.log").read_text())
                    try:
                        if httpx.get(base + "/api/templates").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    time.sleep(0.1)
                else:
                    raise RuntimeError("Browser test server did not become ready")
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(
                        executable_path=shutil.which("chromium") or None, headless=True
                    )
                    context = browser.new_context(
                        viewport={"width": 1440, "height": 1050}, locale="fr-FR"
                    )
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.on(
                        "console",
                        lambda message: (
                            errors.append(message.text) if message.type == "error" else None
                        ),
                    )
                    page.goto(base)
                    expect(page.get_by_role("heading", level=1)).to_have_text(
                        "Moins de correction.Plus de transmission."
                    )
                    page.evaluate("document.fonts.ready")
                    page.screenshot(path=str(args.output / "landing.png"), full_page=True)
                    page.get_by_role("button", name="L’approche", exact=True).click()
                    expect(page.locator("#approach")).to_be_focused()
                    # Skip navigation must not become an application route.
                    page.locator(".skip").focus()
                    page.keyboard.press("Enter")
                    expect(page.locator("#main")).to_be_focused()
                    expect(page.get_by_role("heading", level=1)).to_contain_text("transmission")
                    page.emulate_media(reduced_motion="reduce")
                    assert (
                        page.locator(".scene-composition").evaluate(
                            "el => getComputedStyle(el).animationName"
                        )
                        == "none"
                    )
                    for width in (320, 390, 768):
                        page.set_viewport_size({"width": width, "height": 844})
                        assert page.evaluate(
                            "document.documentElement.scrollWidth <= window.innerWidth"
                        ), f"Landing overflow at {width}px"
                        if width == 390:
                            page.locator("#main").focus()
                            page.evaluate("window.scrollTo(0,0)")
                            page.screenshot(
                                path=str(args.output / "landing-mobile.png"), full_page=True
                            )
                    page.set_viewport_size({"width": 1440, "height": 1050})
                    page.get_by_role("link", name="Ouvrir mon espace").click()
                    expect(
                        page.get_by_role("heading", name="Mes examens", exact=True)
                    ).to_be_visible()
                    page.screenshot(path=str(args.output / "dashboard.png"), full_page=True)
                    page.get_by_role("link", name="Créer un examen").click()
                    page.get_by_label("Nom de l’examen").fill("Examen blanc — Groupe A")
                    page.locator('[data-section-questions="1"]').fill("1-5")
                    page.locator('[data-section-questions="1"]').press("Tab")
                    page.get_by_label("Coller le corrigé de la section 1").fill("2 1 1 2 3")
                    page.get_by_role("button", name="Remplir les réponses").click()
                    expect(page.get_by_role("button", name="Enregistrer l’examen")).to_be_enabled()
                    page.locator("#main").focus()
                    page.evaluate("window.scrollTo(0,0)")
                    page.screenshot(path=str(args.output / "configuration.png"), full_page=True)
                    page.get_by_role("button", name="Enregistrer l’examen").click()
                    expect(
                        page.get_by_role("heading", name="Examen blanc — Groupe A", exact=True)
                    ).to_be_visible()
                    page.locator("#copy-files").set_input_files(root / "data" / "demo" / "copy.png")
                    page.get_by_role("link", name="Voir la correction").wait_for(timeout=30000)
                    page.get_by_role("link", name="Voir la correction").click()
                    expect(page.get_by_text("Note à confirmer", exact=True)).to_be_visible()
                    expect(page.get_by_role("button", name="À vérifier (2)")).to_be_visible()
                    assert page.locator(".crop-view").bounding_box()["height"] <= 300
                    page.screenshot(
                        path=str(args.output / "correction-provisoire.png"), full_page=True
                    )
                    page.get_by_role("button", name="À vérifier (2)").click()
                    page.get_by_role("radio", name="1", exact=True).check()
                    page.get_by_role("button", name="Valider et recalculer").click()
                    expect(page.get_by_role("button", name="À vérifier (1)")).to_be_visible()
                    page.get_by_role("radio", name="2", exact=True).check()
                    page.get_by_role("button", name="Valider et recalculer").click()
                    expect(
                        page.get_by_text("Correction terminée · 12 / 20", exact=True)
                    ).to_be_visible()
                    page.get_by_role("button", name="Toutes les questions (5)").click()
                    # A reload exercises server persistence, not just browser state.
                    page.reload()
                    expect(
                        page.get_by_text("Correction terminée · 12 / 20", exact=True)
                    ).to_be_visible()
                    page.screenshot(path=str(args.output / "correction-finale.png"), full_page=True)
                    with page.expect_download() as download:
                        page.get_by_role("link", name="CSV", exact=True).click()
                    download.value.save_as(args.output / "correction.csv")
                    assert "correct" in (args.output / "correction.csv").read_text(
                        encoding="utf-8-sig"
                    )
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.get_by_role("button", name="S1 · Q3", exact=True).click()
                    expect(page.locator(".review-panel")).to_be_focused()
                    expect(
                        page.get_by_role("button", name="Retour aux questions")
                    ).to_be_in_viewport()
                    page.get_by_role("button", name="Retour aux questions").click()
                    expect(page.get_by_role("button", name="S1 · Q3", exact=True)).to_be_focused()
                    page.evaluate("window.scrollTo(0,0)")
                    page.screenshot(path=str(args.output / "mobile.png"), full_page=True)
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth"
                    ), "Unexpected mobile horizontal overflow"
                    # The landing's action opens a real, reviewable demo, not its illustration.
                    page.goto(base)
                    page.emulate_media(reduced_motion="no-preference")
                    pending_demo = []
                    page.route("**/api/demo", lambda route: pending_demo.append(route))
                    page.get_by_role("button", name="Découvrir la démonstration").click()
                    expect(page.get_by_role("button", name="Analyse en cours…")).to_be_disabled()
                    expect(page.locator("[torph-root]")).to_be_visible()
                    assert pending_demo, "Expected a real demo request"
                    pending_demo.pop().continue_()
                    expect(page.get_by_text("Note à confirmer", exact=True)).to_be_visible(
                        timeout=30000
                    )
                    expect(page.get_by_role("button", name="Valider et recalculer")).to_be_visible()
                    assert page.locator("style[data-torph]").count() == 0, "Torph must clean up"
                    exercise_sheets(page, base, root, args.output)
                    exercise_corpus(page, base, root, args.output)
                    # The corpus deliberately submits one stale revision and asserts its 409.
                    expected_conflict = "Failed to load resource: the server responded with a status of 409 (Conflict)"
                    assert errors.count(expected_conflict) == 1, errors
                    errors.remove(expected_conflict)
                    assert not errors, errors
                    browser.close()
                print(
                    "Browser workflow passed: landing, keyboard, responsive, reduced motion, "
                    "create exam, upload, review, final 12/20, persistence, CSV, real demo, "
                    "manual sheet calibration, test and exam using the new template, corpus annotation, "
                    "manual crops, stale revisions and private export."
                )
            finally:
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
