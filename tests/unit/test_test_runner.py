import pytest
from pathlib import Path
import tempfile
import sys
from harness.tools.test_runner import create_test_runner_handler, parse_pytest_output

def test_parse_pytest_output_pass():
    stdout = "===== 2 passed in 0.05s ====="
    result = parse_pytest_output(stdout, 0)
    assert result["passed"] == 2
    assert result["failed"] == 0
    assert result["signal"] == "pass"

def test_parse_pytest_output_fail():
    stdout = """FAILED tests/test_x.py::test_a - assert 1 == 2
===== 1 failed, 1 passed in 0.05s ====="""
    result = parse_pytest_output(stdout, 1)
    assert result["passed"] == 1
    assert result["failed"] == 1
    assert result["signal"] == "fail"
    assert len(result["failures"]) >= 1

def test_parse_pytest_output_no_tests():
    stdout = "no tests ran"
    result = parse_pytest_output(stdout, 1)
    assert result["passed"] == 0
    assert result["failed"] == 0
    assert result["signal"] == "fail"

@pytest.mark.asyncio
async def test_test_runner_handler():
    with tempfile.TemporaryDirectory() as td:
        test_file = Path(td) / "test_sample.py"
        test_file.write_text("def test_ok():\n    assert True\n")
        handler = create_test_runner_handler(Path(td), timeout=30)
        result = await handler({"test_path": "test_sample.py"})
        assert result.success is True
        assert result.exit_code == 0
