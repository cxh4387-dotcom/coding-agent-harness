import re
import asyncio
import sys
import shutil
from pathlib import Path
from harness.models import ToolResult, Feedback, FailureClass

def parse_pytest_output(stdout: str, exit_code: int) -> dict:
    passed_match = re.search(r"(\d+) passed", stdout)
    failed_match = re.search(r"(\d+) failed", stdout)
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0

    failures = []
    for m in re.finditer(r"FAILED (\S+?)::(\S+?) - (.+)", stdout):
        failures.append(FailureClass(
            type="assertion",
            message=m.group(3),
            location=f"{m.group(1)}::{m.group(2)}"
        ))
    for m in re.finditer(r"ERROR.*?ModuleNotFoundError.*?'(\S+?)'", stdout):
        failures.append(FailureClass(type="import", message=m.group(0), location=""))

    if "no tests ran" in stdout:
        signal = "fail"
    elif failed > 0 or exit_code != 0:
        signal = "fail"
    else:
        signal = "pass"

    return {"passed": passed, "failed": failed, "failures": failures, "signal": signal}

def create_test_runner_handler(workdir: Path, timeout: int = 120):
    async def handler(args: dict) -> ToolResult:
        test_path = args.get("test_path", "")
        cache_dir = workdir / "__pycache__"
        if cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
        cmd = f"{sys.executable} -m pytest {test_path} -v --tb=short 2>&1"
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd, cwd=str(workdir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            output = stdout.decode("utf-8", errors="replace")
            return ToolResult(
                success=proc.returncode == 0,
                stdout=output,
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                content=output,
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
            return ToolResult(success=False, stderr=f"Test timeout after {timeout}s", exit_code=-1)
    return handler
