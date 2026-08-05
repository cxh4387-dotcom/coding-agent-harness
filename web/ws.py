import json
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, task_id: str, ws: WebSocket):
        await ws.accept()
        self.active[task_id] = ws
        await ws.send_json({"type": "connected", "task_id": task_id})

    async def send_action(self, task_id: str, action: dict):
        ws = self.active.get(task_id)
        if ws:
            await ws.send_json({"type": "action", **action})

    async def send_hitl(self, task_id: str, action: dict, danger: str):
        ws = self.active.get(task_id)
        if ws:
            await ws.send_json({"type": "hitl_request", "action": action, "danger": danger})

    async def send_feedback(self, task_id: str, feedback: dict):
        ws = self.active.get(task_id)
        if ws:
            await ws.send_json({"type": "feedback", **feedback})

    async def send_done(self, task_id: str, result: dict):
        ws = self.active.get(task_id)
        if ws:
            await ws.send_json({"type": "done", **result})

    def disconnect(self, task_id: str):
        self.active.pop(task_id, None)

manager = ConnectionManager()
