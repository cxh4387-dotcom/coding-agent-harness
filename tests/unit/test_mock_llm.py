import pytest
from harness.llm.mock import MockLLM
from harness.llm.interface import LLMInterface
from harness.models import ConversationContext, LLMResponse, ToolCall

@pytest.mark.asyncio
async def test_mock_returns_scripted_response():
    resp = LLMResponse(content="hello", tool_calls=[], finish_reason="stop")
    mock = MockLLM(script=[resp])
    ctx = ConversationContext(system="sys", memories=[], history=[], task="test")
    result = await mock.complete(ctx)
    assert result.content == "hello"

@pytest.mark.asyncio
async def test_mock_advances_through_script():
    r1 = LLMResponse(content="first", tool_calls=[], finish_reason="tool_calls")
    r2 = LLMResponse(content="second", tool_calls=[], finish_reason="stop")
    mock = MockLLM(script=[r1, r2])
    ctx = ConversationContext(system="", memories=[], history=[], task="")
    a = await mock.complete(ctx)
    b = await mock.complete(ctx)
    assert a.content == "first"
    assert b.content == "second"

@pytest.mark.asyncio
async def test_mock_raises_on_empty_script():
    mock = MockLLM(script=[])
    ctx = ConversationContext(system="", memories=[], history=[], task="")
    with pytest.raises(IndexError):
        await mock.complete(ctx)

@pytest.mark.asyncio
async def test_mock_records_call_count():
    resp = LLMResponse(content="x", tool_calls=[], finish_reason="stop")
    mock = MockLLM(script=[resp, resp, resp])
    ctx = ConversationContext(system="", memories=[], history=[], task="")
    await mock.complete(ctx)
    await mock.complete(ctx)
    assert mock.call_count == 2
