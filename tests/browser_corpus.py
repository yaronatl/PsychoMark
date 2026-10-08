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
    for index, value in enumerate(["empty", "marked", "empty", "empty"]):
        page.locator(f'[data-mark="{index}"]').select_option(value)
    page.get_by_label("Position de la question", exact=True).select_option("confirmed")
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
    page.get_by_text("Voir l’original et placer un extrait", exact=True).click()
    page.wait_for_function("document.querySelector('#corpus-source-canvas').width > 0")
    page.screenshot(path=str(output / "corpus-annotation.png"), full_page=True)
    for width in (320, 390, 768):
        page.set_viewport_size({"width": width, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
            f"Corpus overflow at {width}"
        )
        if width == 390:
            page.screenshot(path=str(output / "corpus-mobile.png"), full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1050})

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
    page.get_by_label("Votre identifiant de relecture", exact=False).fill("lecteur-A")
    for index in range(4):
        page.locator(f'[data-mark="{index}"]').select_option("unreadable")
    page.get_by_text("Coordonnées du cadre / saisie clavier", exact=True).click()
    for index, value in enumerate([10, 20, 80, 140]):
        page.locator(f'[data-bound="{index}"]').fill(str(value))
    page.get_by_label("Position de la question", exact=True).select_option("confirmed")
    page.get_by_role("button", name="Enregistrer et continuer", exact=True).click()
    expect(page.locator("#corpus-error")).to_contain_text("Appliquez les coordonnées")
    page.get_by_role("button", name="Appliquer les coordonnées", exact=True).click()
    page.get_by_label("Position de la question", exact=True).select_option("confirmed")
    page.get_by_role("button", name="Enregistrer et continuer", exact=True).click()
    expect(page.locator("#corpus-message")).to_contain_text("Observation enregistrée")
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
