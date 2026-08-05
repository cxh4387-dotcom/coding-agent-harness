"""鏈哄埗婕旂ず鈶? 閲嶇偣缁村害(娌荤悊)鐨勭‘瀹氭€ц涓?(搂A.6, 搂A.4-D)
鍦?mock LLM 涓嬬‘瀹氭€у湴澶嶇幇锛歛gent 璇曞浘鍐?sandbox 澶栬矾寰?鈫?琚?Sandbox 鎷︽埅
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
        print(f"鉁?Demo 鈶?PASS: write to /etc/passwd was blocked ({len(result.blocked_actions)} blocked)")

if __name__ == "__main__":
    asyncio.run(main())

