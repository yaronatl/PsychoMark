"""Sequential annotation: proposals are never saved without a fresh human decision."""

import httpx
from playwright.sync_api import expect


def exercise_annotation_flow(parent, base, acquisition, output):
    context = parent.context.browser.new_context(
        viewport={"width": 1440, "height": 1000}, locale="fr-FR"
    )
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    record = httpx.get(f"{base}/api/corpus/{acquisition}").json()
    # Replace the gesture stress-test rectangle with a meaningful synthetic Q2 crop.
    annotation = {
        k: v for k, v in record["questions"][1]["annotation"].items() if k != "recorded_at"
    }
    annotation.update(
        expected_revision=record["revision"],
        section="1",
        question=2,
        manual_bounds=[108, 306, 134, 423],
    )
    response = httpx.patch(f"{base}/api/corpus/{acquisition}/annotations", json=annotation)
    assert response.status_code == 200
    record = response.json()
    page.goto(f"{base}/#/annotations/{acquisition}")
    expect(page.locator("#corpus-question")).to_have_value("2")
    previous = record["questions"][1]["annotation"]["manual_bounds"]
    width = previous[2] - previous[0]
    suggested = [previous[0] + width, previous[1], previous[2] + width, previous[3]]
    page.get_by_label("Mode enchaîné", exact=True).check()
    expect(page.locator("#corpus-manual-preview")).to_be_visible()
    expect(page.locator("#corpus-position")).not_to_be_checked()
    assert page.evaluate("window.psychomarkCanReload()"), (
        "An automatic proposal alone is not a human edit"
    )
    page.get_by_label("Votre identifiant de relecture", exact=True).fill("flow-A")
    page.locator("#corpus-more summary").click()
    page.locator("#corpus-reading").focus()
    # AZERTY number row: physical Digit2 works even when the key is é.
    page.locator("#corpus-reading").dispatch_event(
        "keydown", {"key": "é", "code": "Digit2", "bubbles": True}
    )
    expect(page.locator('[data-quick="2"]')).to_have_attribute("aria-pressed", "true")
    page.keyboard.press("Enter")
    expect(page.locator("#corpus-question")).to_have_value("3")
    stored = httpx.get(f"{base}/api/corpus/{acquisition}").json()["questions"][2]["annotation"]
    assert (
        stored["manual_bounds"] == suggested
        and stored["choices"] == [2]
        and stored["geometry"] == "confirmed"
    )
    assert page.locator("[data-mark]").evaluate_all("els=>els.map(e=>e.value)") == [""] * 4
    expect(page.locator("#corpus-position")).not_to_be_checked()
    # Adjust without a mouse; the crop dialog also accepts arrows and Enter.
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press("c")
    expect(page.get_by_role("dialog")).to_be_visible()
    page.keyboard.press("ArrowLeft")
    adjusted = page.locator("[data-crop-bound]").evaluate_all("els=>els.map(e=>Number(e.value))")
    assert adjusted == [
        suggested[0] + width,
        suggested[1] + 10,
        suggested[2] + width,
        suggested[3] + 10,
    ]
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog")).not_to_be_visible()
    expect(page.locator("#corpus-reading")).to_be_focused()
    page.keyboard.press("Shift+ArrowUp")
    adjusted[1] -= 10
    adjusted[3] -= 10
    page.keyboard.press("Numpad3")
    # Failed save keeps marks and manual geometry, with no advance.
    page.route(
        "**/annotations",
        lambda route: route.fulfill(status=503, json={"detail": "Échec simulé : réessayez."}),
    )
    page.keyboard.press("Enter")
    expect(page.locator("#corpus-error")).to_contain_text("Échec simulé")
    expect(page.locator("#corpus-question")).to_have_value("3")
    expect(page.locator('[data-quick="3"]')).to_have_attribute("aria-pressed", "true")
    page.unroute("**/annotations")
    page.keyboard.down("Enter")
    expect(page.locator("#corpus-question")).to_have_value("4")
    page.keyboard.down("Enter")  # held key must not submit again on the new question
    page.keyboard.up("Enter")
    expect(page.locator("#corpus-error")).to_be_empty()
    stored = httpx.get(f"{base}/api/corpus/{acquisition}").json()["questions"][3]["annotation"]
    assert stored["manual_bounds"] == adjusted and stored["choices"] == [3]
    page.screenshot(path=str(output / "annotation-flow-desktop.png"), full_page=True)
    # Editing notes must not trigger the number-row shortcut.
    page.locator("#corpus-more summary").click()
    page.locator('[name="notes"]').fill("Note ")
    page.locator('[name="notes"]').press("Digit2")
    assert page.locator("[data-mark]").evaluate_all("els=>els.map(e=>e.value)") == [""] * 4
    page.locator('[name="notes"]').fill("")
    page.locator("#corpus-more summary").click()
    # A different section cannot inherit the previous section's rectangle.
    page.once("dialog", lambda d: d.accept())
    page.locator("#corpus-question").select_option("30")
    expect(page.locator("#corpus-manual-preview")).not_to_be_visible()
    page.locator("#corpus-question").select_option("4")
    expect(page.locator("#corpus-manual-preview")).to_be_visible()
    # Mode survives reload, proposals are rebuilt from saved geometry, not tab history.
    page.get_by_label("Sens d’enchaînement").select_option("down")
    page.reload()
    expect(page.get_by_label("Sens d’enchaînement")).to_have_value("down")
    expect(page.get_by_label("Mode enchaîné", exact=True)).to_be_checked()
    expect(page.locator("#corpus-manual-preview")).to_be_visible()
    assert not errors, errors
    context.close()

    mobile = parent.context.browser.new_context(
        viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True
    )
    page = mobile.new_page()
    page.goto(f"{base}/#/annotations/{acquisition}")
    page.get_by_label("Votre identifiant de relecture", exact=True).fill("mobile-flow")
    page.locator("#corpus-more summary").tap()
    page.get_by_label("Mode enchaîné", exact=True).check()
    page.locator(".corpus-toolbar").scroll_into_view_if_needed()
    page.get_by_role("button", name="Seul le choix 4 est marqué", exact=True).tap()
    save = page.get_by_role("button", name="Confirmer et continuer", exact=True)
    expect(save).to_be_in_viewport()
    save.tap()
    expect(page.locator("#corpus-question")).to_have_value("5")
    expect(page.locator("#corpus-context")).to_be_visible()
    assert page.locator("[data-mark]").evaluate_all("els=>els.map(e=>e.value)") == [""] * 4
    for width, height in ((390, 844), (320, 740), (844, 390)):
        page.set_viewport_size({"width": width, "height": height})
        page.locator(".corpus-toolbar").evaluate("el=>el.scrollIntoView({block:'start'})")
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        expect(save).to_be_in_viewport()
        if width <= 390:
            expect(
                page.get_by_role("button", name="Aucune case marquée", exact=True)
            ).to_be_in_viewport()
        if width == 390:
            page.screenshot(path=str(output / "annotation-flow-mobile.png"))
    mobile.close()
