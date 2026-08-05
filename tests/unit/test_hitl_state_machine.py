import pytest
from harness.guardrail.hitl_state_machine import HITLStateMachine, HITLState
from harness.models import Action, DangerRule, GuardrailDecision

def test_initial_state_idle():
    sm = HITLStateMachine(timeout=120)
    assert sm.state == HITLState.IDLE

def test_start_running():
    sm = HITLStateMachine(timeout=120)
    sm.start()
    assert sm.state == HITLState.RUNNING

def test_request_approval():
    sm = HITLStateMachine(timeout=120)
    sm.start()
    action = Action(tool="run_shell", args={"command": "git push --force"}, raw="")
    rule = DangerRule(name="test", matcher=lambda a: True, severity="hitl", reason="test")
    sm.request_approval(action, rule)
    assert sm.state == HITLState.AWAITING_APPROVAL

def test_approve():
    sm = HITLStateMachine(timeout=120)
    sm.start()
    action = Action(tool="run_shell", args={}, raw="")
    rule = DangerRule(name="test", matcher=lambda a: True, severity="hitl", reason="test")
    sm.request_approval(action, rule)
    sm.approve()
    assert sm.state == HITLState.APPROVED
    assert sm.can_proceed() is True

def test_deny():
    sm = HITLStateMachine(timeout=120)
    sm.start()
    action = Action(tool="run_shell", args={}, raw="")
    rule = DangerRule(name="test", matcher=lambda a: True, severity="hitl", reason="test")
    sm.request_approval(action, rule)
    sm.deny()
    assert sm.state == HITLState.DENIED
    assert sm.can_proceed() is False

def test_resume_after_approval():
    sm = HITLStateMachine(timeout=120)
    sm.start()
    action = Action(tool="run_shell", args={}, raw="")
    rule = DangerRule(name="test", matcher=lambda a: True, severity="hitl", reason="test")
    sm.request_approval(action, rule)
    sm.approve()
    sm.resume()
    assert sm.state == HITLState.RUNNING

def test_resume_after_denial():
    sm = HITLStateMachine(timeout=120)
    sm.start()
    action = Action(tool="run_shell", args={}, raw="")
    rule = DangerRule(name="test", matcher=lambda a: True, severity="hitl", reason="test")
    sm.request_approval(action, rule)
    sm.deny()
    sm.resume()
    assert sm.state == HITLState.RUNNING

def test_stop():
    sm = HITLStateMachine(timeout=120)
    sm.start()
    sm.stop()
    assert sm.state == HITLState.STOPPED

def test_pending_action_stored():
    sm = HITLStateMachine(timeout=120)
    sm.start()
    action = Action(tool="run_shell", args={"command": "rm test"}, raw="")
    rule = DangerRule(name="test", matcher=lambda a: True, severity="hitl", reason="test")
    sm.request_approval(action, rule)
    assert sm.pending_action is not None
    assert sm.pending_action.args["command"] == "rm test"
