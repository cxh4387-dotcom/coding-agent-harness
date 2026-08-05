from pathlib import Path
from harness.models import ToolResult

def create_read_file_handler(workdir: Path):
    async def handler(args: dict) -> ToolResult:
        path = workdir / args["path"]
        if not path.exists():
            return ToolResult(success=False, stderr=f"File not found: {path}")
        return ToolResult(success=True, content=path.read_text(encoding="utf-8"))
    return handler

def create_write_file_handler(workdir: Path, max_size: int = 1048576):
    async def handler(args: dict) -> ToolResult:
        path = workdir / args["path"]
        content = args["content"]
        if len(content.encode("utf-8")) > max_size:
            return ToolResult(success=False, stderr=f"File too large: {len(content)} > {max_size}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolResult(success=True)
    return handler
