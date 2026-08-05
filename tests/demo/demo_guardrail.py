"""机制演示①: 治理护栏拦截一个危险动作 (§A.6)
在 mock LLM 下确定性地复现：agent 试图执行 rm -rf / → 被 DangerDetector 拦截
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
            LLMResponse(content="deleting", tool_calls=[
                ToolCall(name="run_shell", arguments={"command": "rm -rf /"})
            ], finish_reason="tool_calls"),
            LLMResponse(content="done", tool_calls=[], finish_reason="stop"),
        ])
        loop = AgentLoop(
            llm=mock_llm, tools=ToolDispatcher(),
            guardrail=DangerDetector(default_rules()),
            hitl=HITLStateMachine(),
            sandbox=Sandbox(workdir=workdir, allowed_paths=[]),
            scope_fence=ScopeFence(ScopeConfig(
                allowed_tools={"run_shell"}, max_iterations=50,
                max_file_size=1048576, forbidden_patterns=[]
            )),
            feedback=FeedbackValidator(),
            memory=MemoryStore(workdir / "mem.json"),
        )
        result = await loop.run("delete everything")
        assert len(result.blocked_actions) == 1
        assert result.blocked_actions[0].decision == "block"
        assert result.blocked_actions[0].rule.name == "rm_rf"
        print("✓ Demo ① PASS: rm -rf / was blocked by DangerDetector")

if __name__ == "__main__":
    asyncio.run(main())
