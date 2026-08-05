"""鏈哄埗婕旂ず鈶? 娉ㄥ叆涓€娆″け璐ワ紝鍙嶉闂幆浣?agent 鏀跺埌鍙嶉骞舵嵁姝ゆ敼鍙樹笅涓€姝ュ姩浣?(搂A.6)
鍦?mock LLM 涓嬬‘瀹氭€у湴澶嶇幇锛歛gent 鍐欓敊璇唬鐮?鈫?娴嬭瘯澶辫触 鈫?鍙嶉鍥炵亴 鈫?agent 淇 鈫?娴嬭瘯閫氳繃
"""
import asyncio
from pathlib import Path
import tempfile
from harness.agent_loop import AgentLoop
from harness.llm.mock import MockLLM
from harness.tools.dispatcher import ToolDispatcher
from harness.tools.file_ops import create_write_file_handler
from harness.tools.test_runner import create_test_runner_handler
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
            LLMResponse(content="write bad", tool_calls=[
                ToolCall(name="write_file", arguments={"path": "test_demo.py", "content": "def test_ok():\n    assert 1 == 2\n"})
            ], finish_reason="tool_calls"),
            LLMResponse(content="run tests", tool_calls=[
                ToolCall(name="run_tests", arguments={"test_path": "test_demo.py"})
            ], finish_reason="tool_calls"),
            LLMResponse(content="fix and rewrite", tool_calls=[
                ToolCall(name="write_file", arguments={"path": "test_demo.py", "content": "def test_ok():\n    assert 1 == 1\n"})
            ], finish_reason="tool_calls"),
            LLMResponse(content="run tests again", tool_calls=[
                ToolCall(name="run_tests", arguments={"test_path": "test_demo.py"})
            ], finish_reason="tool_calls"),
            LLMResponse(content="done", tool_calls=[], finish_reason="stop"),
        ])
        dispatcher = ToolDispatcher()
        dispatcher.register("write_file", create_write_file_handler(workdir))
        dispatcher.register("run_tests", create_test_runner_handler(workdir))
        loop = AgentLoop(
            llm=mock_llm, tools=dispatcher,
            guardrail=DangerDetector(default_rules()),
            hitl=HITLStateMachine(),
            sandbox=Sandbox(workdir=workdir, allowed_paths=[]),
            scope_fence=ScopeFence(ScopeConfig(
                allowed_tools={"write_file", "run_tests"}, max_iterations=50,
                max_file_size=1048576, forbidden_patterns=[]
            )),
            feedback=FeedbackValidator(),
            memory=MemoryStore(workdir / "mem.json"),
        )
        result = await loop.run("write a passing test")
        assert len(result.feedbacks) >= 1
        assert result.final_feedback is not None
        assert result.final_feedback.signal == "pass"
        print(f"鉁?Demo 鈶?PASS: feedback loop corrected code ({len(result.feedbacks)} feedback rounds, final: pass)")

if __name__ == "__main__":
    asyncio.run(main())

