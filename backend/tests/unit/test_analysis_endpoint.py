""" test_analysis_endpoint.py tests the /analyze endpoint of the FastAPI application. """
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"


def test_analyze_valid_file(tmp_path):
    code = "print('hello')\nexec('print(1)')\n"
    p = tmp_path / "sample.py"
    p.write_text(code)

    with open(p, "rb") as f:
        files = {"file": ("sample.py", f, "text/x-python")}
        r = client.post("/api/v1/analyze", files=files)

    assert r.status_code == 200
    body = r.json()
    assert body["filename"] == "sample.py"
    assert body["totalFindings"] >= 1
    assert isinstance(body["findings"], list)

    # Verify persistence via GET /reviews/{id}
    review_id = body.get("id")
    assert review_id is not None
    r2 = client.get(f"/api/v1/reviews/{review_id}")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["filename"] == "sample.py"
    assert data2["totalFindings"] == body["totalFindings"]


def test_analyze_empty_file(tmp_path):
    p = tmp_path / "empty.py"
    p.write_text("")
    with open(p, "rb") as f:
        files = {"file": ("empty.py", f, "text/x-python")}
        r = client.post("/api/v1/analyze", files=files)
    assert r.status_code in (400, 422)


def test_analyze_wrong_extension(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("print('hi')")
    with open(p, "rb") as f:
        files = {"file": ("sample.txt", f, "text/plain")}
        r = client.post("/api/v1/analyze", files=files)
    assert r.status_code == 400
