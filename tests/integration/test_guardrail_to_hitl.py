"""Integration test: guardrail detects danger → HITL state machine pauses → approve → execute"""
import pytest
from pathlib import Path
import tempfile
from harness.guardrail.danger_detector import DangerDetector, default_rules
from harness.guardrail.hitl_state_machine import HITLStateMachine, HITLState
from harness.models import Action

def test_guardrail_to_hitl_flow():
    detector = DangerDetector(default_rules())
    sm = HITLStateMachine()
    sm.start()

    action = Action(tool="run_shell", args={"command": "git push --force"}, raw="")
    decision = detector.check(action)

    assert decision.decision == "hitl"
    sm.request_approval(action, decision.rule)
    assert sm.state == HITLState.AWAITING_APPROVAL

    sm.approve()
    assert sm.can_proceed() is True
    sm.resume()
    assert sm.state == HITLState.RUNNING

def test_guardrail_to_hitl_deny():
    detector = DangerDetector(default_rules())
    sm = HITLStateMachine()
    sm.start()

    action = Action(tool="run_shell", args={"command": "git push --force"}, raw="")
    decision = detector.check(action)

    sm.request_approval(action, decision.rule)
    sm.deny()
    assert sm.can_proceed() is False
    sm.resume()
    assert sm.state == HITLState.RUNNING
