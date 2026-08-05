"""机制演示③: 重点维度(治理)的确定性行为 (§A.6, §A.4-D)
在 mock LLM 下确定性地复现：agent 试图写 sandbox 外路径 → 被 Sandbox 拦截
"""
import asyncio
from pathlib import Path
import tempfile
from harness.agent_loop import AgentLoop
from harness.llm.mock import MockLLM
from harness.tools.dispatcher import ToolDispatcher
from harness.guardrail.danger_detector import DangerDetector, default_rules
from harness.guardrail.hitl_state_machine import HITLStateMachine
from harness.guardrail.sandbox import Sandbox
from harness.guardrail.scope_fence import ScopeFence, ScopeConfig
from harness.feedback import FeedbackValidator
from harness.memory import MemoryStore
from harness.models import LLMResponse, ToolCall

async def main():
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        mock_llm = MockLLM(script=[
            LLMResponse(content="write outside", tool_calls=[
                ToolCall(name="write_file", arguments={"path": "/etc/passwd", "content": "hacked"})
            ], finish_reason="tool_calls"),
            LLMResponse(content="done", tool_calls=[], finish_reason="stop"),
        ])
        loop = AgentLoop(
            llm=mock_llm, tools=ToolDispatcher(),
            guardrail=DangerDetector(default_rules()),
            hitl=HITLStateMachine(),
            sandbox=Sandbox(workdir=workdir, allowed_paths=[]),
            scope_fence=ScopeFence(ScopeConfig(
                allowed_tools={"write_file"}, max_iterations=50,
                max_file_size=1048576, forbidden_patterns=[]
            )),
            feedback=FeedbackValidator(),
            memory=MemoryStore(workdir / "mem.json"),
        )
        result = await loop.run("write to system file")
        assert len(result.blocked_actions) >= 1
        print(f"✓ Demo ③ PASS: write to /etc/passwd was blocked ({len(result.blocked_actions)} blocked)")

if __name__ == "__main__":
    asyncio.run(main())
