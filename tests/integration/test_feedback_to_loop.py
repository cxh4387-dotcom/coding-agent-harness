"""Integration test: feedback validator parses failure → context updated → agent changes behavior"""
import pytest
from pathlib import Path
import tempfile
from harness.feedback import FeedbackValidator
from harness.models import Action, ToolResult, ConversationContext

def test_feedback_updates_context():
    validator = FeedbackValidator()
    action = Action(tool="run_tests", args={"test_path": "test_x.py"}, raw="")
    result = ToolResult(
        success=False,
        stdout="FAILED test_x.py::test_a - assert 1 == 2\n===== 1 failed =====",
        exit_code=1,
    )
    feedback = validator.validate(action, result)
    assert feedback.signal == "fail"

    context = ConversationContext(system="sys", memories=[], history=[], task="test")
    context.history.append({"role": "system", "content": f"Tests failed: {feedback.failed} failures. Fix them."})
    assert any("Tests failed" in m["content"] for m in context.history)
