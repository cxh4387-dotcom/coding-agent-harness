import pytest
import re
from harness.guardrail.scope_fence import ScopeFence, ScopeConfig
from harness.models import Action

def test_allow_within_limits():
    config = ScopeConfig(allowed_tools={"read_file", "write_file"}, max_iterations=50, max_file_size=1048576, forbidden_patterns=[])
    fence = ScopeFence(config)
    action = Action(tool="read_file", args={"path": "test.py"}, raw="")
    result = fence.enforce(action, iteration=10)
    assert result.allowed is True

def test_block_unknown_tool():
    config = ScopeConfig(allowed_tools={"read_file"}, max_iterations=50, max_file_size=1048576, forbidden_patterns=[])
    fence = ScopeFence(config)
    action = Action(tool="run_shell", args={}, raw="")
    result = fence.enforce(action, iteration=1)
    assert result.allowed is False
    assert "not allowed" in result.reason.lower()

def test_block_max_iterations():
    config = ScopeConfig(allowed_tools={"read_file"}, max_iterations=50, max_file_size=1048576, forbidden_patterns=[])
    fence = ScopeFence(config)
    action = Action(tool="read_file", args={}, raw="")
    result = fence.enforce(action, iteration=51)
    assert result.allowed is False
    assert "iteration" in result.reason.lower()

def test_block_forbidden_pattern():
    config = ScopeConfig(allowed_tools={"run_shell"}, max_iterations=50, max_file_size=1048576, forbidden_patterns=[re.compile(r"rm\s+-rf")])
    fence = ScopeFence(config)
    action = Action(tool="run_shell", args={"command": "rm -rf /"}, raw="")
    result = fence.enforce(action, iteration=1)
    assert result.allowed is False
    assert "forbidden" in result.reason.lower()

def test_block_file_too_large():
    config = ScopeConfig(allowed_tools={"write_file"}, max_iterations=50, max_file_size=10, forbidden_patterns=[])
    fence = ScopeFence(config)
    action = Action(tool="write_file", args={"content": "x" * 100}, raw="")
    result = fence.enforce(action, iteration=1)
    assert result.allowed is False
    assert "size" in result.reason.lower() or "large" in result.reason.lower()
