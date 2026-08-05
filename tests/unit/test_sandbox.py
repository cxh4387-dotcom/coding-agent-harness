import pytest
from pathlib import Path
from harness.guardrail.sandbox import Sandbox

def test_validate_path_inside_workdir():
    sb = Sandbox(workdir=Path("/tmp/workspace"), allowed_paths=[])
    assert sb.validate_path(Path("/tmp/workspace/src/main.py")) is True

def test_validate_path_outside_workdir():
    sb = Sandbox(workdir=Path("/tmp/workspace"), allowed_paths=[])
    assert sb.validate_path(Path("/etc/passwd")) is False

def test_validate_path_allowed_paths():
    sb = Sandbox(workdir=Path("/tmp/workspace"), allowed_paths=[Path("/tmp/shared")])
    assert sb.validate_path(Path("/tmp/shared/data.txt")) is True

def test_validate_path_parent_traversal():
    sb = Sandbox(workdir=Path("/tmp/workspace"), allowed_paths=[])
    assert sb.validate_path(Path("/tmp/workspace/../etc/passwd")) is False

def test_validate_command_safe():
    sb = Sandbox(workdir=Path("/tmp/workspace"), allowed_paths=[])
    assert sb.validate_command("ls -la") is True

def test_validate_command_cd_escape():
    sb = Sandbox(workdir=Path("/tmp/workspace"), allowed_paths=[])
    assert sb.validate_command("cd ../../etc && cat passwd") is False

def test_validate_command_absolute_path():
    sb = Sandbox(workdir=Path("/tmp/workspace"), allowed_paths=[])
    assert sb.validate_command("cat /etc/passwd") is False
