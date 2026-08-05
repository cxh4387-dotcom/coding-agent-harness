import uuid
from fastapi import APIRouter, Request
from pydantic import BaseModel

class TaskRequest(BaseModel):
    task: str

class CredentialRequest(BaseModel):
    api_key: str

def create_router() -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/health")
    async def health():
        return {"status": "ok"}

    @router.post("/tasks")
    async def create_task(req: TaskRequest, request: Request):
        task_id = str(uuid.uuid4())
        request.app.state.tasks[task_id] = {"task": req.task, "status": "pending"}
        return {"task_id": task_id, "status": "pending"}

    @router.get("/tasks/{task_id}")
    async def get_task(task_id: str, request: Request):
        task = request.app.state.tasks.get(task_id, {})
        return {"task_id": task_id, **task}

    @router.post("/tasks/{task_id}/approve")
    async def approve_task(task_id: str, request: Request):
        return {"task_id": task_id, "approved": True}

    @router.post("/tasks/{task_id}/deny")
    async def deny_task(task_id: str, request: Request):
        return {"task_id": task_id, "denied": True}

    @router.get("/credentials/status")
    async def cred_status(request: Request):
        cm = request.app.state.cred_manager
        return {"has_key": cm.has_key()}

    @router.post("/credentials")
    async def store_cred(req: CredentialRequest, request: Request):
        cm = request.app.state.cred_manager
        cm.store_key(req.api_key)
        return {"stored": True}

    @router.delete("/credentials")
    async def delete_cred(request: Request):
        cm = request.app.state.cred_manager
        cm.delete_key()
        return {"deleted": True}

    @router.get("/config")
    async def get_config():
        return {"config": "todo"}

    return router
