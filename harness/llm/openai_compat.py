import json
import httpx
from harness.llm.interface import LLMInterface
from harness.models import ConversationContext, LLMResponse, ToolCall

class OpenAICompatibleLLM(LLMInterface):
    def __init__(self, base_url: str, api_key: str, model: str,
                 temperature: float = 0.7, max_tokens: int = 4096):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def complete(self, context: ConversationContext) -> LLMResponse:
        messages = self._build_messages(context)
        raw = await self._raw_call(messages)
        return self._parse_response(raw)

    async def _raw_call(self, messages: list[dict]) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {"model": self.model, "messages": messages,
                "temperature": self.temperature, "max_tokens": self.max_tokens}
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{self.base_url}/chat/completions",
                                     headers=headers, json=body)
            resp.raise_for_status()
            return resp.json()

    def _build_messages(self, ctx: ConversationContext) -> list[dict]:
        messages = [{"role": "system", "content": ctx.system}]
        for m in ctx.memories:
            messages.append({"role": "system", "content": m})
        messages.extend(ctx.history)
        messages.append({"role": "user", "content": ctx.task})
        return messages

    def _parse_response(self, raw: dict) -> LLMResponse:
        choice = raw["choices"][0]
        msg = choice["message"]
        tool_calls = []
        for tc in (msg.get("tool_calls") or []):
            args = json.loads(tc["function"]["arguments"])
            tool_calls.append(ToolCall(name=tc["function"]["name"], arguments=args))
        return LLMResponse(
            content=msg.get("content") or "",
            tool_calls=tool_calls,
            finish_reason=choice["finish_reason"]
        )
