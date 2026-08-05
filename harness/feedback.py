import re
from harness.models import Action, ToolResult, Feedback, FailureClass
from harness.tools.test_runner import parse_pytest_output

class FeedbackValidator:
    def validate(self, action: Action, result: ToolResult) -> Feedback | None:
        if action.tool == "run_tests":
            return self._validate_tests(result)
        return None

    def _validate_tests(self, result: ToolResult) -> Feedback:
        parsed = parse_pytest_output(result.stdout, result.exit_code)
        failures = parsed["failures"]
        if re.search(r"SyntaxError", result.stdout):
            m = re.search(r"File '([^']+)', line (\d+)", result.stdout)
            loc = f"{m.group(1)}:{m.group(2)}" if m else ""
            failures.append(FailureClass(type="syntax", message="SyntaxError", location=loc))
        return Feedback(
            passed=parsed["passed"],
            failed=parsed["failed"],
            failures=failures,
            signal=parsed["signal"],
        )
