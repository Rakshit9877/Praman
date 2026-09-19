from fastapi.testclient import TestClient
from backend.app.main import app
import os

os.environ["AI_MODE"] = "mock"

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] == True
    assert response.json()["ai_mode"] == "mock"

def test_wage_table():
    response = client.get("/api/wage-table")
    assert response.status_code == 200

def test_job_lifecycle():
    # Create session
    resp = client.post("/api/workers/session")
    assert resp.status_code == 200
    w_id = resp.json()["worker_id"]

    # Start job
    resp = client.post("/api/registers", data={"worker_id": w_id}, files={"image": ("test.jpg", b"123", "image/jpeg")})
    assert resp.status_code == 200
    j_id = resp.json()["job_id"]
    
    # Poll job
    resp = client.get(f"/api/jobs/{j_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"
    
    resp = client.get(f"/api/jobs/{j_id}")
    assert resp.status_code == 200
    
    resp = client.get(f"/api/jobs/{j_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
