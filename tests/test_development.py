from fastapi.testclient import TestClient

from psychomark.development import codespaces_origin, source_revision
from psychomark.web import create_app


def test_codespaces_origin_uses_platform_metadata(monkeypatch):
    monkeypatch.setenv("CODESPACES", "true")
    monkeypatch.setenv("CODESPACE_NAME", "sample-project-123")
    monkeypatch.setenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
    assert codespaces_origin(8000) == "https://sample-project-123-8000.app.github.dev"
    monkeypatch.setenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "evil.example/path")
    assert codespaces_origin(8000) is None
    monkeypatch.delenv("CODESPACES")
    assert codespaces_origin(8000) is None


def test_source_revision_includes_assets_but_ignores_generated_data(tmp_path):
    css = tmp_path / "style.css"
    css.write_text("body { color: black; }")
    first = source_revision(tmp_path)
    (tmp_path / "database.sqlite3").write_bytes(b"generated")
    assert source_revision(tmp_path) == first
    css.write_text("body { color: blue; }")
    assert source_revision(tmp_path) != first


def test_private_forwarded_origin_can_write_without_accepting_arbitrary_hosts(sheet, tmp_path):
    origin = "https://example-codespace-8000.app.github.dev"
    app = create_app(tmp_path, [sheet["template_path"]], external_origin=origin)
    exam = {
        "name": "Proxy test",
        "template_id": sheet["layout"].template_id,
        "sections": {"1": [1]},
        "answer_key": {"1": {"1": 2}},
    }
    with TestClient(app) as client:
        assert client.post("/api/exams", json=exam, headers={"Origin": origin}).status_code == 201
        assert (
            client.post(
                "/api/exams",
                json=exam,
                headers={"Origin": "https://evil.example", "X-Forwarded-Host": "evil.example"},
            ).status_code
            == 403
        )
        assert client.get("/api/health").json() == {"app": "psychomark", "development": False}
        assert client.get("/api/dev/revision").status_code == 404
        assert "live.js" not in client.get("/").text
        # Only Torph's exact, locally built stylesheet is allowed inline.
        from psychomark.web import TORPH_STYLE_HASH

        policy = client.get("/").headers["Content-Security-Policy"]
        assert f"'sha256-{TORPH_STYLE_HASH}'" in policy
        assert "'unsafe-inline'" not in policy
        assert client.get("/assets/vendor/torph.mjs").status_code == 200


def test_development_mode_serves_live_reload_separately(sheet, tmp_path):
    with TestClient(create_app(tmp_path, [sheet["template_path"]], development=True)) as client:
        assert client.get("/api/health").json()["development"] is True
        assert len(client.get("/api/dev/revision").json()["revision"]) == 64
        assert 'src="/assets/live.js"' in client.get("/").text
        assert client.get("/assets/live.js").status_code == 200
