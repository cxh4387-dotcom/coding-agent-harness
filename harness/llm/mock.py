from harness.llm.interface import LLMInterface
from harness.models import ConversationContext, LLMResponse

class MockLLM(LLMInterface):
    """Returns pre-scripted responses for deterministic testing."""
    def __init__(self, script: list[LLMResponse]):
        self._script = script
        self._step = 0
        self.call_count = 0

    async def complete(self, context: ConversationContext) -> LLMResponse:
        if self._step >= len(self._script):
            raise IndexError(f"MockLLM script exhausted after {self._step} calls")
        resp = self._script[self._step]
        self._step += 1
        self.call_count += 1
        return resp
