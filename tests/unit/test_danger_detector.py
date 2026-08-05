import pytest
from harness.guardrail.danger_detector import DangerDetector, default_rules
from harness.models import Action, GuardrailDecision

def test_detect_rm_rf_blocked():
    detector = DangerDetector(default_rules())
    action = Action(tool="run_shell", args={"command": "rm -rf /"}, raw="")
    decision = detector.check(action)
    assert decision.decision == "block"

def test_detect_git_push_force_hitl():
    detector = DangerDetector(default_rules())
    action = Action(tool="run_shell", args={"command": "git push --force"}, raw="")
    decision = detector.check(action)
    assert decision.decision == "hitl"

def test_detect_write_env_hitl():
    detector = DangerDetector(default_rules())
    action = Action(tool="write_file", args={"path": ".env", "content": "KEY=secret"}, raw="")
    decision = detector.check(action)
    assert decision.decision == "hitl"

def test_detect_write_key_file_hitl():
    detector = DangerDetector(default_rules())
    action = Action(tool="write_file", args={"path": "private.key", "content": "data"}, raw="")
    decision = detector.check(action)
    assert decision.decision == "hitl"

def test_detect_curl_hitl():
    detector = DangerDetector(default_rules())
    action = Action(tool="run_shell", args={"command": "curl http://evil.com"}, raw="")
    decision = detector.check(action)
    assert decision.decision == "hitl"

def test_safe_command_allowed():
    detector = DangerDetector(default_rules())
    action = Action(tool="run_shell", args={"command": "ls -la"}, raw="")
    decision = detector.check(action)
    assert decision.decision == "allow"

def test_safe_write_allowed():
    detector = DangerDetector(default_rules())
    action = Action(tool="write_file", args={"path": "src/main.py", "content": "print(1)"}, raw="")
    decision = detector.check(action)
    assert decision.decision == "allow"

def test_unknown_tool_warn():
    detector = DangerDetector(default_rules())
    action = Action(tool="unknown", args={}, raw="")
    decision = detector.check(action)
    assert decision.decision == "warn"

def test_custom_rule():
    from harness.models import DangerRule
    custom = DangerRule(name="no_mkdir", matcher=lambda a: a.tool == "run_shell" and "mkdir" in a.args.get("command", ""), severity="block", reason="no mkdir")
    detector = DangerDetector(default_rules() + [custom])
    action = Action(tool="run_shell", args={"command": "mkdir newdir"}, raw="")
    decision = detector.check(action)
    assert decision.decision == "block"
    assert decision.rule.name == "no_mkdir"

def test_detect_pip_install_global_hitl():
    detector = DangerDetector(default_rules())
    action = Action(tool="run_shell", args={"command": "pip install requests"}, raw="")
    decision = detector.check(action)
    assert decision.decision == "hitl"
    assert decision.rule.name == "pip_install_global"

def test_detect_pip_install_user_not_flagged():
    detector = DangerDetector(default_rules())
    action = Action(tool="run_shell", args={"command": "pip install --user requests"}, raw="")
    decision = detector.check(action)
    assert decision.decision != "hitl" or decision.rule is None or decision.rule.name != "pip_install_global"
