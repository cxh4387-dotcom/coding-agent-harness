import pytest
from pathlib import Path
import tempfile
from harness.tools.file_ops import create_read_file_handler, create_write_file_handler

@pytest.mark.asyncio
async def test_read_file_success():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "test.txt"
        p.write_text("hello world")
        handler = create_read_file_handler(Path(td))
        result = await handler({"path": "test.txt"})
        assert result.success is True
        assert result.content == "hello world"

@pytest.mark.asyncio
async def test_read_file_not_found():
    with tempfile.TemporaryDirectory() as td:
        handler = create_read_file_handler(Path(td))
        result = await handler({"path": "nonexistent.txt"})
        assert result.success is False
        assert "not found" in result.stderr.lower() or "no such file" in result.stderr.lower()

@pytest.mark.asyncio
async def test_write_file_success():
    with tempfile.TemporaryDirectory() as td:
        handler = create_write_file_handler(Path(td), max_size=1048576)
        result = await handler({"path": "out.txt", "content": "written content"})
        assert result.success is True
        assert (Path(td) / "out.txt").read_text() == "written content"

@pytest.mark.asyncio
async def test_write_file_too_large():
    with tempfile.TemporaryDirectory() as td:
        handler = create_write_file_handler(Path(td), max_size=10)
        result = await handler({"path": "big.txt", "content": "x" * 100})
        assert result.success is False
        assert "size" in result.stderr.lower() or "too large" in result.stderr.lower()
