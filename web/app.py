from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from web.api import create_router
from web.ws import manager as ws_manager
from harness.credentials import CredentialManager
import json
from fastapi import WebSocket, WebSocketDisconnect

def create_app(workdir: Path, config_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Coding Agent Harness")
    vault_path = workdir / ".harness" / "vault.enc"
    cred_manager = CredentialManager(vault_path=vault_path)
    app.state.workdir = workdir
    app.state.cred_manager = cred_manager
    app.state.tasks = {}
    app.include_router(create_router())
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.websocket("/ws/tasks/{task_id}")
    async def websocket_endpoint(websocket: WebSocket, task_id: str):
        await ws_manager.connect(task_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                if msg.get("type") == "approve":
                    pass
                elif msg.get("type") == "deny":
                    pass
        except WebSocketDisconnect:
            ws_manager.disconnect(task_id)

    @app.get("/")
    async def index():
        return FileResponse(str(Path(__file__).parent / "static" / "index.html"))

    return app


app = create_app(workdir=Path("/app/workspace"))

