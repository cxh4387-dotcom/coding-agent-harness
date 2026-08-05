from dataclasses import dataclass, field
from typing import Callable, Literal

@dataclass
class Action:
    tool: str
    args: dict
    raw: str = ""

@dataclass
class ToolResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    content: str = ""

@dataclass
class DangerRule:
    name: str
    matcher: Callable[["Action"], bool]
    severity: Literal["block", "hitl", "warn"]
    reason: str

@dataclass
class GuardrailDecision:
    action: Action
    rule: DangerRule | None
    decision: Literal["allow", "block", "hitl", "warn"]

@dataclass
class FailureClass:
    type: Literal["assertion", "import", "timeout", "syntax"]
    message: str
    location: str

@dataclass
class Feedback:
    passed: int
    failed: int
    failures: list[FailureClass]
    signal: Literal["pass", "fail"]

@dataclass
class ToolCall:
    name: str
    arguments: dict

@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall]
    finish_reason: Literal["stop", "tool_calls", "length"]

@dataclass
class AgentResult:
    actions: list[Action]
    results: list[ToolResult]
    feedbacks: list[Feedback]
    blocked_actions: list[GuardrailDecision]
    iterations: int
    final_feedback: Feedback | None = None

@dataclass
class ConversationContext:
    system: str
    memories: list[str]
    history: list[dict]
    task: str

@dataclass
class FenceResult:
    allowed: bool
    reason: str = ""

@dataclass
class Memory:
    id: str
    task: str
    decision: str
    rationale: str
    timestamp: str
    tags: list[str]
