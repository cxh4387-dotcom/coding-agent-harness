import pytest
from pathlib import Path
import tempfile
from harness.agent_loop import AgentLoop
from harness.llm.mock import MockLLM
from harness.tools.dispatcher import ToolDispatcher
from harness.tools.file_ops import create_write_file_handler
from harness.guardrail.danger_detector import DangerDetector, default_rules
from harness.guardrail.hitl_state_machine import HITLStateMachine
from harness.guardrail.sandbox import Sandbox
from harness.guardrail.scope_fence import ScopeFence, ScopeConfig
from harness.feedback import FeedbackValidator
from harness.memory import MemoryStore
from harness.models import LLMResponse, ToolCall, Action

@pytest.mark.asyncio
async def test_agent_loop_writes_file_and_stops():
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        mock_llm = MockLLM(script=[
            LLMResponse(content="writing file", tool_calls=[
                ToolCall(name="write_file", arguments={"path": "out.txt", "content": "hello"})
            ], finish_reason="tool_calls"),
            LLMResponse(content="done", tool_calls=[], finish_reason="stop"),
        ])
        dispatcher = ToolDispatcher()
        dispatcher.register("write_file", create_write_file_handler(workdir))
        loop = AgentLoop(
            llm=mock_llm,
            tools=dispatcher,
            guardrail=DangerDetector(default_rules()),
            hitl=HITLStateMachine(),
            sandbox=Sandbox(workdir=workdir, allowed_paths=[]),
            scope_fence=ScopeFence(ScopeConfig(
                allowed_tools={"write_file", "read_file", "run_shell", "run_tests"},
                max_iterations=50, max_file_size=1048576, forbidden_patterns=[]
            )),
            feedback=FeedbackValidator(),
            memory=MemoryStore(workdir / "mem.json"),
        )
        result = await loop.run("write hello to out.txt")
        assert result.iterations == 2
        assert (workdir / "out.txt").read_text() == "hello"

@pytest.mark.asyncio
async def test_agent_loop_blocks_dangerous_action():
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        mock_llm = MockLLM(script=[
            LLMResponse(content="deleting", tool_calls=[
                ToolCall(name="run_shell", arguments={"command": "rm -rf /"})
            ], finish_reason="tool_calls"),
            LLMResponse(content="done", tool_calls=[], finish_reason="stop"),
        ])
        dispatcher = ToolDispatcher()
        loop = AgentLoop(
            llm=mock_llm,
            tools=dispatcher,
            guardrail=DangerDetector(default_rules()),
            hitl=HITLStateMachine(),
            sandbox=Sandbox(workdir=workdir, allowed_paths=[]),
            scope_fence=ScopeFence(ScopeConfig(
                allowed_tools={"write_file", "read_file", "run_shell", "run_tests"},
                max_iterations=50, max_file_size=1048576, forbidden_patterns=[]
            )),
            feedback=FeedbackValidator(),
            memory=MemoryStore(workdir / "mem.json"),
        )
        result = await loop.run("delete everything")
        assert len(result.blocked_actions) == 1
        assert result.blocked_actions[0].decision == "block"

@pytest.mark.asyncio
async def test_agent_loop_max_iterations():
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        resp = LLMResponse(content="loop", tool_calls=[
            ToolCall(name="write_file", arguments={"path": "a.txt", "content": "x"})
        ], finish_reason="tool_calls")
        mock_llm = MockLLM(script=[resp] * 100)
        dispatcher = ToolDispatcher()
        dispatcher.register("write_file", create_write_file_handler(workdir))
        loop = AgentLoop(
            llm=mock_llm,
            tools=dispatcher,
            guardrail=DangerDetector(default_rules()),
            hitl=HITLStateMachine(),
            sandbox=Sandbox(workdir=workdir, allowed_paths=[]),
            scope_fence=ScopeFence(ScopeConfig(
                allowed_tools={"write_file"},
                max_iterations=3, max_file_size=1048576, forbidden_patterns=[]
            )),
            feedback=FeedbackValidator(),
            memory=MemoryStore(workdir / "mem.json"),
        )
        result = await loop.run("loop forever")
        assert result.iterations <= 4
