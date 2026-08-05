import pytest
from pathlib import Path
import tempfile
from fastapi.testclient import TestClient
from web.app import create_app

def test_websocket_connect():
    app = create_app(workdir=Path(tempfile.mkdtemp()))
    client = TestClient(app)
    with client.websocket_connect("/ws/tasks/test-123") as ws:
        data = ws.receive_json()
        assert "type" in data

def test_websocket_receives_action_messages():
    app = create_app(workdir=Path(tempfile.mkdtemp()))
    client = TestClient(app)
    with client.websocket_connect("/ws/tasks/test-456") as ws:
        msg = ws.receive_json()
        assert msg["type"] in ("connected", "action", "hitl_request", "feedback", "done")
