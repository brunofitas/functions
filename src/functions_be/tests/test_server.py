from fastapi.testclient import TestClient

from functions_be.server import build_app


def test_build_app_without_gui_serves_api(tmp_path):
    app, token = build_app(base_dir=str(tmp_path), token="tok")
    assert token == "tok"
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 404  # no GUI mounted


def test_build_app_with_gui_serves_studio(tmp_path):
    gui = tmp_path / "gui"
    (gui / "dist").mkdir(parents=True)
    (gui / "index.html").write_text("<html>token=__TOKEN__</html>")
    (gui / "dist" / "studio.js").write_text("console.log('studio')")
    app, _ = build_app(base_dir=str(tmp_path), gui_dir=str(gui), token="tok")
    client = TestClient(app)

    page = client.get("/")
    assert page.status_code == 200
    assert "token=tok" in page.text and "__TOKEN__" not in page.text  # token injected

    js = client.get("/studio.js")
    assert js.status_code == 200 and "studio" in js.text
