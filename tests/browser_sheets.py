"""Browser exercise of the manual sheet workflow using synthetic pixels only."""

import json
import zipfile
from pathlib import Path

import cv2
import numpy as np
from playwright.sync_api import Page, expect


def exercise_sheets(page: Page, base: str, root: Path, output: Path) -> None:
    page.set_viewport_size({"width": 1440, "height": 1050})
    page.goto(base + "/#/sheets")
    page.get_by_role("link", name="Ajouter une feuille", exact=True).click()
    expect(page.get_by_role("heading", name="Ajouter une feuille", exact=True)).to_be_visible()
    page.get_by_label("Fichier de la feuille").set_input_files(
        root / "data" / "demo" / "template.reference.png"
    )
    page.get_by_role("button", name="Importer la feuille", exact=True).click()
    expect(page.get_by_role("heading", name="Décrire une grille")).to_be_visible()
    page.get_by_label("Nom de la feuille", exact=True).fill("Feuille du navigateur")
    layout = json.loads((root / "data" / "demo" / "template.json").read_text())
    s = layout["sections"][0]
    page.get_by_label("Questions imprimées").fill(str(s["questions"]))
    page.get_by_label("Choix par question").fill(str(s["choices"]))
    page.get_by_label("Demi-largeur case (px)").fill(str(s["bubble_radius"][0]))
    page.get_by_label("Demi-hauteur case (px)").fill(str(s["bubble_radius"][1]))
    x, y, w, h = s["bounds"]
    cx, cy = s["first_center"]
    points = [
        (x, y),
        (x + w, y + h),
        (cx, cy),
        (cx + (s["questions"] - 1) * s["question_step"][0], cy),
        (cx, cy + (s["choices"] - 1) * s["choice_step"][1]),
    ]
    canvas = page.locator("#sheet-canvas")
    page.wait_for_function("document.querySelector('#sheet-canvas').width === 1800")
    for px, py in points:
        box = canvas.bounding_box()
        canvas.click(
            position={
                "x": px / layout["width"] * box["width"],
                "y": py / layout["height"] * box["height"],
            }
        )
    expect(page.locator("#sheet-guide")).to_contain_text("cinq repères")
    # Pointer precision can be subpixel; numeric refinement is also keyboard accessible.
    page.get_by_text("Coordonnées précises / saisie clavier", exact=True).click()
    for i, (px, py) in enumerate(points):
        page.locator(f'[name="point-{i}-x"]').fill(str(px))
        page.locator(f'[name="point-{i}-y"]').fill(str(py))
    page.get_by_role("button", name="Ajouter la grille", exact=True).click()
    expect(page.locator("#sheet-sections")).to_contain_text("Section 1")
    assert page.evaluate("window.psychomarkCanReload()") is False
    # Declining navigation preserves the local geometry.
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.locator("#nav-exams").click()
    expect(page.locator("#sheet-sections")).to_contain_text("Section 1")
    page.evaluate("window.scrollTo(0,0)")
    page.screenshot(path=str(output / "sheet-editor.png"), full_page=True)
    for width in (320, 390, 768):
        page.set_viewport_size({"width": width, "height": 844})
        if page.evaluate("document.documentElement.scrollWidth > innerWidth"):
            page.screenshot(path=str(output / "sheet-overflow.png"), full_page=True)
            print(
                page.evaluate(
                    "Array.from(document.querySelectorAll('body *')).filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>[e.tagName,e.id,e.className,e.getBoundingClientRect().width]).slice(0,30)"
                )
            )
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
    page.screenshot(path=str(output / "sheet-mobile.png"), full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1050})
    page.get_by_role("button", name="Vérifier et sauvegarder les zones").click()
    expect(page.get_by_role("heading", name="Vérifier les cases repérées")).to_be_visible(
        timeout=30000
    )
    page.wait_for_function("window.psychomarkCanReload()")
    page.reload()
    expect(page.get_by_role("heading", name="Vérifier les cases repérées")).to_be_visible()
    # Real refusals from the engine: first failed alignment, then an aligned page
    # whose printed frame was damaged. Neither should be presented as blank answers.
    empty = root / "empty.png"
    cv2.imwrite(str(empty), np.full((1320, 1800, 3), 255, dtype=np.uint8))
    page.get_by_label("Copie à essayer", exact=True).set_input_files(empty)
    page.get_by_role("button", name="Analyser cette copie").click()
    expect(page.get_by_role("heading", name="Alignement non confirmé")).to_be_visible(timeout=30000)
    expect(
        page.get_by_text("Trop peu de repères reconnaissables dans la photo", exact=True)
    ).to_be_visible()
    page.wait_for_function("window.psychomarkCanReload()")
    page.reload()
    expect(page.get_by_role("heading", name="Alignement non confirmé")).to_be_visible()
    with page.expect_download() as download:
        page.get_by_role("link", name="Télécharger le diagnostic (images incluses)").click()
    download.value.save_as(output / "sheet-diagnostic.zip")
    with zipfile.ZipFile(output / "sheet-diagnostic.zip") as bundle:
        assert "copy.png" in bundle.namelist()
        assert "template.reference.png" in bundle.namelist()
    damaged = cv2.imread(str(root / "data" / "demo" / "copy.png"))
    cv2.rectangle(damaged, (int(x), int(y)), (int(x + w), int(y + h)), (255, 255, 255), 10)
    damaged_path = root / "frame-damaged.png"
    cv2.imwrite(str(damaged_path), damaged)
    page.get_by_label("Copie à essayer", exact=True).set_input_files(damaged_path)
    page.get_by_role("button", name="Analyser cette copie").click()
    expect(page.get_by_role("heading", name="Alignement réussi")).to_be_visible(timeout=30000)
    expect(
        page.get_by_text(
            "Le contour des grilles ne correspond pas assez à la référence", exact=True
        )
    ).to_be_visible()
    page.get_by_text("Détail technique du diagnostic", exact=True).click()
    expect(page.locator(".sheet-diagnostic")).to_contain_text("frame_support")
    page.screenshot(path=str(output / "sheet-unreadable.png"), full_page=True)
    page.get_by_label("Copie à essayer", exact=True).set_input_files(
        root / "data" / "demo" / "copy.png"
    )
    page.get_by_role("button", name="Analyser cette copie").click()
    expect(page.locator("#sheet-test-results tbody tr")).to_have_count(30, timeout=30000)
    expect(page.locator("#sheet-test-results tbody tr").first).to_contain_text(
        "Réponse unique", timeout=30000
    )
    expect(page.locator("#sheet-test-results tbody tr").nth(2)).to_contain_text("Plusieurs marques")
    page.screenshot(path=str(output / "sheet-test.png"), full_page=True)
    page.get_by_label("J’ai vérifié l’emplacement de toutes les cases sur l’aperçu.").check()
    page.get_by_role("button", name="Enregistrer le modèle", exact=True).click()
    expect(page.get_by_role("link", name="Créer un examen avec cette feuille")).to_be_visible(
        timeout=30000
    )
    page.get_by_role("link", name="Créer un examen avec cette feuille").click()
    expect(page.locator("#template-select option:checked")).to_have_text("Feuille du navigateur")
    # The existing exam editor allows selecting fewer questions than the paper contains.
    page.locator('[data-section-questions="1"]').fill("1-5")
    page.locator('[data-section-questions="1"]').press("Tab")
    page.get_by_label("Nom de l’examen").fill("Examen sur ma feuille")
    page.get_by_label("Coller le corrigé de la section 1").fill("2 1 1 2 3")
    page.get_by_role("button", name="Remplir les réponses").click()
    page.get_by_role("button", name="Enregistrer l’examen").click()
    expect(page.get_by_role("heading", name="Examen sur ma feuille", exact=True)).to_be_visible()
    page.locator("#copy-files").set_input_files(root / "data" / "demo" / "copy.png")
    page.get_by_role("link", name="Voir la correction").wait_for(timeout=30000)
    page.get_by_role("link", name="Voir la correction").click()
    expect(page.get_by_role("button", name="À vérifier (2)")).to_be_visible()
