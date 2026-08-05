import re
from dataclasses import dataclass, field
from harness.models import Action, FenceResult

@dataclass
class ScopeConfig:
    allowed_tools: set[str]
    max_iterations: int
    max_file_size: int
    forbidden_patterns: list[re.Pattern] = field(default_factory=list)

class ScopeFence:
    def __init__(self, config: ScopeConfig):
        self.config = config

    def enforce(self, action: Action, iteration: int) -> FenceResult:
        if action.tool not in self.config.allowed_tools:
            return FenceResult(allowed=False, reason=f"Tool '{action.tool}' is not allowed")
        if iteration > self.config.max_iterations:
            return FenceResult(allowed=False, reason=f"Max iterations ({self.config.max_iterations}) exceeded")
        for pattern in self.config.forbidden_patterns:
            raw = str(action.args)
            if pattern.search(raw):
                return FenceResult(allowed=False, reason=f"Forbidden pattern matched: {pattern.pattern}")
        if action.tool == "write_file":
            content = action.args.get("content", "")
            if len(content.encode("utf-8")) > self.config.max_file_size:
                return FenceResult(allowed=False, reason=f"File too large: {len(content)} > {self.config.max_file_size}")
        return FenceResult(allowed=True)
