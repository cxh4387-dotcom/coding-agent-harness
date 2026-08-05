from abc import ABC, abstractmethod
from harness.models import ConversationContext, LLMResponse

class LLMInterface(ABC):
    @abstractmethod
    async def complete(self, context: ConversationContext) -> LLMResponse:
        """Single chat completion. Returns structured response."""
        ...
