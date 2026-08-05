import asyncio
import asyncio.subprocess
from harness.models import ToolResult

def create_shell_handler(timeout: int = 30):
    async def handler(args: dict) -> ToolResult:
        command = args["command"]
        proc = None
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return ToolResult(
                success=proc.returncode == 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
            )
        except asyncio.TimeoutError:
            if proc is not None:
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass
                try:
                    proc._transport.close()
                except Exception:
                    pass
            return ToolResult(success=False, stderr=f"Command timeout after {timeout}s", exit_code=-1)
    return handler
