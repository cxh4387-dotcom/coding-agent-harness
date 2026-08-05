import pytest
from pathlib import Path
import tempfile
from fastapi.testclient import TestClient
from web.app import create_app

def test_app_health():
    app = create_app(workdir=Path(tempfile.mkdtemp()))
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_submit_task():
    app = create_app(workdir=Path(tempfile.mkdtemp()))
    client = TestClient(app)
    resp = client.post("/api/tasks", json={"task": "write a function"})
    assert resp.status_code == 200
    assert "task_id" in resp.json()

def test_get_task_status():
    app = create_app(workdir=Path(tempfile.mkdtemp()))
    client = TestClient(app)
    resp = client.post("/api/tasks", json={"task": "test"})
    task_id = resp.json()["task_id"]
    resp = client.get(f"/api/tasks/{task_id}")
    assert resp.status_code == 200

def test_credential_status():
    app = create_app(workdir=Path(tempfile.mkdtemp()))
    client = TestClient(app)
    resp = client.get("/api/credentials/status")
    assert resp.status_code == 200
    assert "has_key" in resp.json()

def test_store_and_delete_credential():
    app = create_app(workdir=Path(tempfile.mkdtemp()))
    client = TestClient(app)
    resp = client.post("/api/credentials", json={"api_key": "sk-test-12345"})
    assert resp.status_code == 200
    resp = client.get("/api/credentials/status")
    assert resp.json()["has_key"] is True
    resp = client.delete("/api/credentials")
    assert resp.status_code == 200
    resp = client.get("/api/credentials/status")
    assert resp.json()["has_key"] is False
