import re
from harness.models import Action, DangerRule, GuardrailDecision

class DangerDetector:
    def __init__(self, rules: list[DangerRule]):
        self._rules = rules

    def check(self, action: Action) -> GuardrailDecision:
        for rule in self._rules:
            if rule.matcher(action):
                return GuardrailDecision(action=action, rule=rule, decision=rule.severity)
        if action.tool not in ("read_file", "write_file", "run_shell", "run_tests"):
            return GuardrailDecision(action=action, rule=None, decision="warn")
        return GuardrailDecision(action=action, rule=None, decision="allow")

def default_rules() -> list[DangerRule]:
    return [
        DangerRule(
            name="rm_rf",
            matcher=lambda a: a.tool == "run_shell" and bool(re.search(r"rm\s+-rf", a.args.get("command", ""))),
            severity="block",
            reason="rm -rf is destructive",
        ),
        DangerRule(
            name="del_recursive",
            matcher=lambda a: a.tool == "run_shell" and bool(re.search(r"del\s+/[sS]", a.args.get("command", ""))),
            severity="block",
            reason="recursive delete is destructive",
        ),
        DangerRule(
            name="git_push_force",
            matcher=lambda a: a.tool == "run_shell" and bool(re.search(r"git\s+push\s+--force", a.args.get("command", ""))),
            severity="hitl",
            reason="force push rewrites history",
        ),
        DangerRule(
            name="write_env",
            matcher=lambda a: a.tool == "write_file" and a.args.get("path", "").endswith(".env"),
            severity="hitl",
            reason="writing .env may expose secrets",
        ),
        DangerRule(
            name="write_key_file",
            matcher=lambda a: a.tool == "write_file" and bool(re.search(r"\.(key|pem)$", a.args.get("path", ""))),
            severity="hitl",
            reason="writing key/cert file",
        ),
        DangerRule(
            name="curl_wget",
            matcher=lambda a: a.tool == "run_shell" and bool(re.search(r"\b(curl|wget)\b", a.args.get("command", ""))),
            severity="hitl",
            reason="outbound network request",
        ),
        DangerRule(
            name="npm_publish",
            matcher=lambda a: a.tool == "run_shell" and bool(re.search(r"npm\s+publish", a.args.get("command", ""))),
            severity="hitl",
            reason="publishing to registry",
        ),
        DangerRule(
            name="pip_install_global",
            matcher=lambda a: a.tool == "run_shell" and bool(re.search(r"pip\s+install", a.args.get("command", ""))) and not bool(re.search(r"--user", a.args.get("command", ""))),
            severity="hitl",
            reason="global pip install may modify system packages",
        ),
    ]
