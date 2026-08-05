from enum import Enum
from harness.models import Action, DangerRule

class HITLState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    DENIED = "denied"
    STOPPED = "stopped"

class HITLStateMachine:
    def __init__(self, timeout: int = 120):
        self.timeout = timeout
        self.state = HITLState.IDLE
        self.pending_action: Action | None = None
        self.pending_rule: DangerRule | None = None

    def start(self):
        self.state = HITLState.RUNNING

    def request_approval(self, action: Action, rule: DangerRule):
        self.state = HITLState.AWAITING_APPROVAL
        self.pending_action = action
        self.pending_rule = rule

    def approve(self):
        self.state = HITLState.APPROVED

    def deny(self):
        self.state = HITLState.DENIED

    def resume(self):
        self.state = HITLState.RUNNING
        self.pending_action = None
        self.pending_rule = None

    def stop(self):
        self.state = HITLState.STOPPED

    def can_proceed(self) -> bool:
        return self.state == HITLState.APPROVED
