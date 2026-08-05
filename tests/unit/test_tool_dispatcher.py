import pytest
from harness.tools.dispatcher import ToolDispatcher
from harness.models import Action, ToolResult

@pytest.mark.asyncio
async def test_dispatch_calls_registered_handler():
    dispatcher = ToolDispatcher()
    async def handler(args):
        return ToolResult(success=True, content=f"read {args['path']}")
    dispatcher.register("read_file", handler)
    action = Action(tool="read_file", args={"path": "test.py"}, raw="")
    result = await dispatcher.dispatch(action)
    assert result.success is True
    assert "test.py" in result.content

@pytest.mark.asyncio
async def test_dispatch_unknown_tool_returns_error():
    dispatcher = ToolDispatcher()
    action = Action(tool="unknown_tool", args={}, raw="")
    result = await dispatcher.dispatch(action)
    assert result.success is False
    assert "unknown_tool" in result.stderr

@pytest.mark.asyncio
async def test_dispatch_handler_exception_caught():
    dispatcher = ToolDispatcher()
    async def bad_handler(args):
        raise RuntimeError("boom")
    dispatcher.register("bad", bad_handler)
    action = Action(tool="bad", args={}, raw="")
    result = await dispatcher.dispatch(action)
    assert result.success is False
    assert "boom" in result.stderr
