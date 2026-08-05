import traceback
from harness.models import Action, ToolResult

class ToolDispatcher:
    def __init__(self):
        self._handlers: dict[str, callable] = {}

    def register(self, tool_name: str, handler):
        self._handlers[tool_name] = handler

    async def dispatch(self, action: Action) -> ToolResult:
        handler = self._handlers.get(action.tool)
        if handler is None:
            return ToolResult(success=False, stderr=f"Unknown tool: {action.tool}")
        try:
            return await handler(action.args)
        except Exception as e:
            return ToolResult(success=False, stderr=f"{e}\n{traceback.format_exc()}")
