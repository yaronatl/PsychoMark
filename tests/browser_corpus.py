"""Human annotation workflow; synthetic images only, no hidden answer-key hints."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import cv2
import httpx
import numpy as np
from playwright.sync_api import Page, expect


def exercise_corpus(page: Page, base: str, root: Path, output: Path) -> None:
    page.set_viewport_size({"width": 1440, "height": 1050})
    demo = root / "data" / "demo"
    page.goto(base + "/#/annotations")
    expect(page.get_by_role("heading", name="Annotations", exact=True)).to_be_visible()
    page.get_by_role("link", name="Ajouter une copie", exact=True).first.click()
    page.get_by_label("Photo ou diagnostic", exact=True).set_input_files(demo / "copy.png")
    physical_id = page.get_by_label("Identifiant de la feuille papier", exact=True)
    physical_id.fill("invalid alias")
    assert not physical_id.evaluate("el => el.checkValidity()")
    physical_id.fill("papier-001")
    assert physical_id.evaluate("el => el.checkValidity()")
    page.get_by_role("button", name="Importer et annoter", exact=True).click()
    expect(page.get_by_role("heading", name="Feuille papier-001", exact=True)).to_be_visible()
    acquisition = page.url.split("/")[-1]
    expect(page.locator("[data-mark]")).to_have_count(4)
    assert all(
        value == ""
        for value in page.locator("[data-mark]").evaluate_all("els=>els.map(e=>e.value)")
    )
    assert "Réponse attendue" not in page.locator(".corpus").inner_text()
    page.get_by_label("Votre identifiant de relecture", exact=False).fill("lecteur-A")
    page.get_by_role("button", name="Seul le choix 2 est marqué", exact=True).click()
    assert page.locator("[data-mark]").evaluate_all("els=>els.map(e=>e.value)") == [
        "empty",
        "marked",
        "empty",
        "empty",
    ]
    page.locator("#corpus-position").check()
    assert page.evaluate("window.psychomarkCanReload()") is False
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.locator("#nav-exams").click()
    expect(page.get_by_role("heading", name="Feuille papier-001", exact=True)).to_be_visible()
    page.get_by_role("button", name="Enregistrer et continuer", exact=True).click()
    expect(page.locator("#corpus-message")).to_contain_text("Observation enregistrée")
    expect(page.locator("#corpus-question")).to_have_value("1")
    assert page.evaluate("window.psychomarkCanReload()") is True
    page.reload()
    expect(page.locator("#corpus-question")).to_have_value("1")
    page.locator("#corpus-question").select_option("0")
    expect(page.locator('[data-mark="1"]')).to_have_value("marked")
    expect(page.locator(".corpus")).to_contain_text("1 / 240 questions observées")

    page.screenshot(path=str(output / "corpus-annotation.png"), full_page=True)
    for width in (320, 390, 768):
        page.set_viewport_size({"width": width, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
            f"Corpus overflow at {width}"
        )
        if width == 390:
            page.screenshot(path=str(output / "corpus-mobile.png"), full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1050})

    # Keyboard shortcuts do not intercept typing in an annotation field.
    page.locator("#corpus-reading").focus()
    page.keyboard.press("0")
    assert page.locator("[data-mark]").evaluate_all("els=>els.map(e=>e.value)") == ["empty"] * 4
    page.keyboard.press("2")
    page.locator("#corpus-more").evaluate("el=>el.open=true")
    page.locator('[name="notes"]').fill("Observation 1")
    page.locator('[name="notes"]').press("3")
    assert page.locator("[data-mark]").evaluate_all("els=>els.map(e=>e.value)") == [
        "empty",
        "marked",
        "empty",
        "empty",
    ]

    # A stale tab must not silently overwrite a human observation.
    record = httpx.get(f"{base}/api/corpus/{acquisition}").json()
    annotation = record["questions"][0]["annotation"]
    payload = {k: v for k, v in annotation.items() if k != "recorded_at"}
    payload.update(
        expected_revision=record["revision"], section="1", question=1, reviewer="lecteur-B"
    )
    assert (
        httpx.patch(f"{base}/api/corpus/{acquisition}/annotations", json=payload).status_code == 200
    )
    page.locator("#corpus-more").evaluate("el=>el.open=true")
    page.get_by_label("Votre identifiant de relecture", exact=False).fill("lecteur-A")
    with page.expect_response(
        lambda response: (
            response.url.endswith(f"/{acquisition}/annotations")
            and response.request.method == "PATCH"
        )
    ) as stale_response:
        page.get_by_role("button", name="Enregistrer et continuer", exact=True).click()
    assert stale_response.value.status == 409
    expect(page.locator("#corpus-error")).to_contain_text("changé")
    expect(page.locator('[data-mark="1"]')).to_have_value("marked")
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#nav-annotations").click()

    # A failed registration is annotatable from the source; manual geometry is explicit.
    template = json.loads((demo / "template.json").read_text())
    blank = np.full((template["height"], template["width"], 3), 255, np.uint8)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("template.json", json.dumps(template))
        bundle.writestr("template.reference.png", (demo / "template.reference.png").read_bytes())
        bundle.writestr("copy.png", cv2.imencode(".png", blank)[1].tobytes())
        bundle.writestr(
            "result.json",
            json.dumps({"exam": {"template_id": template["template_id"], "sections": {"1": [1]}}}),
        )
    page.get_by_role("link", name="Ajouter une copie", exact=True).click()
    page.get_by_label("Photo ou diagnostic", exact=True).set_input_files(
        {"name": "diagnostic.zip", "mimeType": "application/zip", "buffer": archive.getvalue()}
    )
    expect(page.locator('[name="template_id"]')).to_be_disabled()
    expect(page.locator('[name="split"]')).to_be_disabled()
    page.get_by_label("Identifiant de la feuille papier", exact=True).fill("papier-002")
    page.get_by_role("button", name="Importer et annoter", exact=True).click()
    expect(page.get_by_role("heading", name="Feuille papier-002", exact=True)).to_be_visible()
    expect(page.locator(".corpus")).to_contain_text("Aucun extrait positionné")
    # Alias is retained per tab; detailed ambiguous/illegible states remain available.
    expect(page.locator('[name="reviewer"]')).to_have_value("lecteur-A")
    page.get_by_text("Plusieurs marques ou une trace douteuse", exact=True).click()
    for index in range(4):
        page.locator(f'[data-mark="{index}"]').select_option("unreadable")
    page.get_by_role("button", name="Cadrer cette question", exact=True).click()
    page.get_by_text("Coordonnées / alternative au glissement", exact=True).click()
    for index, value in enumerate([10, 20, 80, 140]):
        page.locator(f'[data-crop-bound="{index}"]').fill(str(value))
    page.get_by_role("button", name="Utiliser ce cadre", exact=True).click()
    expect(page.locator(".crop-editor .error")).to_contain_text("Appliquez les coordonnées")
    page.get_by_role("button", name="Appliquer les coordonnées", exact=True).click()
    page.get_by_role("button", name="Utiliser ce cadre", exact=True).click()
    expect(page.locator("#corpus-position")).to_be_checked()
    page.get_by_role("button", name="Enregistrer et continuer", exact=True).click()
    expect(page.locator("#corpus-message")).to_contain_text("Toutes les questions sont observées")
    expect(page.locator(".corpus")).to_contain_text("Extrait placé manuellement")
    expect(page.locator(".corpus")).to_contain_text("1 / 1 questions observées")
    with page.expect_download() as download:
        page.get_by_role("link", name="Exporter cette copie", exact=True).click()
    exported = zipfile.ZipFile(download.value.path())
    manifest = json.loads(exported.read("manifest.json"))
    assert manifest["split"] == "development"
    assert manifest["questions"][0]["annotation"]["manual_bounds"] == [10, 20, 80, 140]
    assert not manifest["eligible_for_training"]
    assert "extraction.json" not in exported.namelist()
    page.screenshot(path=str(output / "corpus-manual.png"), full_page=True)

    exercise_mobile_corpus(page, base, acquisition, output)


def exercise_mobile_corpus(parent: Page, base: str, acquisition: str, output: Path) -> None:
    """Chromium touch input, not just a narrow desktop viewport."""
    context = parent.context.browser.new_context(
        viewport={"width": 390, "height": 844},
        is_mobile=True,
        has_touch=True,
        device_scale_factor=2,
        locale="fr-FR",
    )
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console", lambda message: errors.append(message.text) if message.type == "error" else None
    )
    cdp = context.new_cdp_session(page)

    def drag(x0, y0, x1, y1, cancel=False):
        cdp.send(
            "Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y0}]}
        )
        for step in range(1, 6):
            cdp.send(
                "Input.dispatchTouchEvent",
                {
                    "type": "touchMove",
                    "touchPoints": [
                        {"x": x0 + (x1 - x0) * step / 5, "y": y0 + (y1 - y0) * step / 5}
                    ],
                },
            )
        cdp.send(
            "Input.dispatchTouchEvent",
            {"type": "touchCancel" if cancel else "touchEnd", "touchPoints": []},
        )

    def bounds():
        return page.locator("[data-crop-bound]").evaluate_all("els=>els.map(e=>Number(e.value))")

    page.goto(f"{base}/#/annotations/{acquisition}")
    expect(page.locator("#corpus-question")).to_have_value("1")
    page.get_by_label("Votre identifiant de relecture", exact=True).fill("mobile-A")
    page.locator("#corpus-more summary").tap()
    page.get_by_role("button", name="Seul le choix 3 est marqué", exact=True).tap()
    page.get_by_role("button", name="Enregistrer et continuer", exact=True).tap()
    expect(page.locator("#corpus-error")).to_contain_text("confirmez sa position")
    # A quick choice never silently validates automatic geometry or saves labels.
    assert (
        httpx.get(f"{base}/api/corpus/{acquisition}").json()["questions"][1]["annotation"] is None
    )
    page.get_by_role("button", name="Ajuster le cadre", exact=True).tap()
    expect(page.get_by_role("dialog")).to_be_visible()
    page.get_by_label("Zoom de la photo", exact=True).select_option("3")
    page.locator(".crop-viewport").evaluate("el=>{el.scrollLeft=0;el.scrollTop=0}")
    box = page.locator(".crop-viewport").bounding_box()
    x, y = box["x"] + 30, box["y"] + 25
    drag(x, y, x + 100, y + 120)
    first = bounds()
    assert first[2] > first[0] and first[3] > first[1]
    # Move inside the frame, then resize its bottom-right corner.
    drag(x + 50, y + 60, x + 70, y + 80)
    moved = bounds()
    assert moved[0] > first[0] and moved[2] - moved[0] == first[2] - first[0]
    drag(x + 120, y + 140, x + 140, y + 160)
    resized = bounds()
    assert resized[2] > moved[2] and resized[3] > moved[3]
    drag(x + 70, y + 80, x + 80, y + 90, cancel=True)
    assert bounds() == resized, "Cancelled touch must restore the previous rectangle"
    page.screenshot(path=str(output / "corpus-touch-crop.png"))
    # Pan mode must scroll the image without changing the crop.
    page.get_by_role("button", name="Déplacer la photo", exact=True).tap()
    before = page.locator(".crop-viewport").evaluate("el=>el.scrollTop")
    drag(x + 50, y + 150, x + 50, y + 40)
    page.wait_for_function("document.querySelector('.crop-viewport').scrollTop > 0")
    assert page.locator(".crop-viewport").evaluate("el=>el.scrollTop") > before
    assert bounds() == resized
    # Native scrolling may consume the next tap while momentum is still running.
    page.locator(".crop-viewport").evaluate("""async el => {
        let previous=el.scrollTop, stable=0;
        for(let i=0;i<180 && stable<6;i++) {
            await new Promise(requestAnimationFrame);
            stable=el.scrollTop===previous?stable+1:0; previous=el.scrollTop;
        }
    }""")
    page.get_by_role("button", name="Utiliser ce cadre", exact=True).tap()
    expect(page.get_by_role("dialog")).not_to_be_visible()
    expect(page.locator("#corpus-position")).to_be_checked()
    expect(page.locator("#corpus-manual-preview")).to_be_visible()
    save = page.get_by_role("button", name="Enregistrer et continuer", exact=True)
    expect(save).to_be_in_viewport()
    # Repeated taps during a delayed save result in one PATCH only.
    pending = []
    page.route(
        "**/annotations",
        lambda route: (
            pending.append(route) if route.request.method == "PATCH" else route.continue_()
        ),
    )
    save.tap()
    expect(save).to_be_disabled()
    box = save.bounding_box()
    page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    assert len(pending) == 1
    pending[0].continue_()
    expect(page.locator("#corpus-question")).to_have_value("2")
    stored = httpx.get(f"{base}/api/corpus/{acquisition}").json()["questions"][1]["annotation"]
    assert stored["manual_bounds"] == resized and stored["choices"] == [3]
    assert page.locator("[data-mark]").evaluate_all("els=>els.map(e=>e.value)") == [""] * 4
    expect(page.locator("#corpus-position")).not_to_be_checked()
    # The previous size is opt-in and cancellable; no mark or confirmation carries over.
    page.get_by_role("button", name="Ajuster le cadre", exact=True).tap()
    page.get_by_role("button", name="Reprendre le dernier cadre", exact=True).tap()
    assert bounds() == resized
    page.get_by_role("button", name="Annuler", exact=True).tap()
    assert page.evaluate("window.psychomarkCanReload()") is True
    page.get_by_role("button", name="Revoir la dernière", exact=True).tap()
    expect(page.locator("#corpus-question")).to_have_value("1")
    expect(
        page.get_by_role("button", name="Seul le choix 3 est marqué", exact=True)
    ).to_have_attribute("aria-pressed", "true")
    for width, height in ((320, 740), (390, 844), (844, 390)):
        page.set_viewport_size({"width": width, "height": height})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
            f"Overflow at {width}"
        )
        if width == 390:
            page.evaluate("scrollTo(0,0)")
            page.screenshot(path=str(output / "corpus-fast-mobile.png"), full_page=True)
    assert not errors, errors
    context.close()
