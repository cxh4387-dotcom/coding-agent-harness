import pytest
import sys
from harness.tools.shell import create_shell_handler

@pytest.mark.asyncio
async def test_shell_echo():
    handler = create_shell_handler(timeout=5)
    cmd = f'"{sys.executable}" -c "print(\'hello\')"'
    result = await handler({"command": cmd})
    assert result.success is True
    assert "hello" in result.stdout

@pytest.mark.asyncio
async def test_shell_failure():
    handler = create_shell_handler(timeout=5)
    cmd = f'"{sys.executable}" -c "import sys; sys.exit(1)"'
    result = await handler({"command": cmd})
    assert result.success is False
    assert result.exit_code == 1

@pytest.mark.asyncio
async def test_shell_timeout():
    handler = create_shell_handler(timeout=1)
    cmd = f'"{sys.executable}" -c "import time; time.sleep(10)"'
    result = await handler({"command": cmd})
    assert result.success is False
    assert "timeout" in result.stderr.lower() or result.exit_code == -1
