from harness.models import (
    Action, ToolResult, GuardrailDecision, Feedback,
    LLMResponse, ToolCall, AgentResult, ConversationContext,
    FenceResult,
)
from harness.llm.interface import LLMInterface
from harness.tools.dispatcher import ToolDispatcher
from harness.guardrail.danger_detector import DangerDetector
from harness.guardrail.hitl_state_machine import HITLStateMachine, HITLState
from harness.guardrail.sandbox import Sandbox
from harness.guardrail.scope_fence import ScopeFence
from harness.feedback import FeedbackValidator
from harness.memory import MemoryStore


class AgentLoop:
    def __init__(
        self,
        llm: LLMInterface,
        tools: ToolDispatcher,
        guardrail: DangerDetector,
        hitl: HITLStateMachine,
        sandbox: Sandbox,
        scope_fence: ScopeFence,
        feedback: FeedbackValidator,
        memory: MemoryStore,
    ):
        self.llm = llm
        self.tools = tools
        self.guardrail = guardrail
        self.hitl = hitl
        self.sandbox = sandbox
        self.scope_fence = scope_fence
        self.feedback = feedback
        self.memory = memory

    async def run(self, task: str) -> AgentResult:
        self.hitl.start()
        context = self.memory.build_context(task)
        actions: list[Action] = []
        results: list[ToolResult] = []
        feedbacks: list[Feedback] = []
        blocked: list[GuardrailDecision] = []
        iteration = 0
        final_feedback = None

        while iteration < self.scope_fence.config.max_iterations:
            iteration += 1
            response = await self.llm.complete(context)

            if response.finish_reason == "stop" and not response.tool_calls:
                break

            for tc in response.tool_calls:
                action = Action(tool=tc.name, args=tc.arguments, raw=str(tc))
                actions.append(action)

                decision = self.guardrail.check(action)
                if decision.decision == "block":
                    blocked.append(decision)
                    context.history.append({"role": "system", "content": f"BLOCKED: {decision.rule.reason}"})
                    continue
                if decision.decision == "hitl":
                    self.hitl.request_approval(action, decision.rule)
                    context.history.append({"role": "system", "content": f"HITL pending: {decision.rule.reason}"})
                    continue

                fence_result = self.scope_fence.enforce(action, iteration)
                if not fence_result.allowed:
                    blocked.append(GuardrailDecision(action=action, rule=None, decision="block"))
                    context.history.append({"role": "system", "content": f"FENCE: {fence_result.reason}"})
                    continue

                result = await self.tools.dispatch(action)
                results.append(result)
                context.history.append({"role": "tool", "content": result.stdout or result.stderr or ("ok" if result.success else "error")})

                fb = self.feedback.validate(action, result)
                if fb:
                    feedbacks.append(fb)
                    final_feedback = fb
                    if fb.signal == "fail":
                        context.history.append({"role": "system", "content": f"Tests failed: {fb.failed} failures. Fix them."})

            if response.finish_reason == "stop":
                break

        return AgentResult(
            actions=actions,
            results=results,
            feedbacks=feedbacks,
            blocked_actions=blocked,
            iterations=iteration,
            final_feedback=final_feedback,
        )
