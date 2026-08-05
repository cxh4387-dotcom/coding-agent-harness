"""鏈哄埗婕旂ず鈶? 娌荤悊鎶ゆ爮鎷︽埅涓€涓嵄闄╁姩浣?(搂A.6)
鍦?mock LLM 涓嬬‘瀹氭€у湴澶嶇幇锛歛gent 璇曞浘鎵ц rm -rf / 鈫?琚?DangerDetector 鎷︽埅
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
        print("鉁?Demo 鈶?PASS: rm -rf / was blocked by DangerDetector")

if __name__ == "__main__":
    asyncio.run(main())

