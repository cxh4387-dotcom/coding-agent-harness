import pytest
from harness.feedback import FeedbackValidator
from harness.models import Action, ToolResult

def test_validate_tests_pass():
    validator = FeedbackValidator()
    action = Action(tool="run_tests", args={"test_path": "test_x.py"}, raw="")
    result = ToolResult(success=True, stdout="===== 2 passed in 0.05s =====", exit_code=0)
    feedback = validator.validate(action, result)
    assert feedback.signal == "pass"
    assert feedback.passed == 2
    assert feedback.failed == 0

def test_validate_tests_fail():
    validator = FeedbackValidator()
    action = Action(tool="run_tests", args={"test_path": "test_x.py"}, raw="")
    result = ToolResult(success=False, stdout="FAILED test_x.py::test_a - assert 1 == 2\n===== 1 failed, 1 passed =====", exit_code=1)
    feedback = validator.validate(action, result)
    assert feedback.signal == "fail"
    assert feedback.failed == 1
    assert len(feedback.failures) >= 1
    assert feedback.failures[0].type == "assertion"

def test_validate_write_file_no_feedback():
    validator = FeedbackValidator()
    action = Action(tool="write_file", args={"path": "a.py"}, raw="")
    result = ToolResult(success=True)
    feedback = validator.validate(action, result)
    assert feedback is None

def test_validate_syntax_error():
    validator = FeedbackValidator()
    action = Action(tool="run_tests", args={"test_path": "test_x.py"}, raw="")
    result = ToolResult(success=False, stdout="SyntaxError: invalid syntax\n  File 'a.py', line 1", exit_code=1)
    feedback = validator.validate(action, result)
    assert feedback.signal == "fail"
    assert any(f.type == "syntax" for f in feedback.failures)
