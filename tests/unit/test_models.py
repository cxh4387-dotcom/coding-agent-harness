from harness.models import (
    Action, ToolResult, GuardrailDecision, Feedback, FailureClass,
    LLMResponse, ToolCall, AgentResult, ConversationContext,
    DangerRule, FenceResult
)

def test_action_creation():
    a = Action(tool="read_file", args={"path": "/tmp/test.py"}, raw='{"tool":"read_file"}')
    assert a.tool == "read_file"
    assert a.args["path"] == "/tmp/test.py"

def test_tool_result_defaults():
    r = ToolResult(success=True)
    assert r.stdout == ""
    assert r.exit_code == 0

def test_guardrail_decision_allow():
    a = Action(tool="read_file", args={}, raw="")
    d = GuardrailDecision(action=a, rule=None, decision="allow")
    assert d.decision == "allow"
    assert d.rule is None

def test_feedback_signal():
    f = Feedback(passed=3, failed=0, failures=[], signal="pass")
    assert f.signal == "pass"

def test_failure_class():
    fc = FailureClass(type="assertion", message="assert 1 == 2", location="test.py:5")
    assert fc.type == "assertion"

def test_llm_response_with_tool_calls():
    tc = ToolCall(name="write_file", arguments={"path": "a.py", "content": "x"})
    r = LLMResponse(content="writing file", tool_calls=[tc], finish_reason="tool_calls")
    assert len(r.tool_calls) == 1
    assert r.tool_calls[0].name == "write_file"

def test_agent_result():
    r = AgentResult(actions=[], results=[], feedbacks=[], blocked_actions=[], iterations=0, final_feedback=None)
    assert r.iterations == 0
    assert r.final_feedback is None

def test_conversation_context():
    ctx = ConversationContext(system="you are a coder", memories=[], history=[], task="write a function")
    assert ctx.system == "you are a coder"
    assert ctx.task == "write a function"

def test_danger_rule():
    rule = DangerRule(name="rm_rf", matcher=lambda a: True, severity="block", reason="dangerous")
    assert rule.severity == "block"

def test_fence_result():
    fr = FenceResult(allowed=False, reason="max iterations exceeded")
    assert not fr.allowed
