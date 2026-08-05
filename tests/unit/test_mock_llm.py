import pytest
from harness.llm.mock import MockLLM
from harness.llm.interface import LLMInterface
from harness.models import ConversationContext, LLMResponse, ToolCall

def test_mock_returns_scripted_response():
    resp = LLMResponse(content="hello", tool_calls=[], finish_reason="stop")
    mock = MockLLM(script=[resp])
    ctx = ConversationContext(system="sys", memories=[], history=[], task="test")
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(mock.complete(ctx))
    assert result.content == "hello"

def test_mock_advances_through_script():
    r1 = LLMResponse(content="first", tool_calls=[], finish_reason="tool_calls")
    r2 = LLMResponse(content="second", tool_calls=[], finish_reason="stop")
    mock = MockLLM(script=[r1, r2])
    ctx = ConversationContext(system="", memories=[], history=[], task="")
    import asyncio
    loop = asyncio.new_event_loop()
    a = loop.run_until_complete(mock.complete(ctx))
    b = loop.run_until_complete(mock.complete(ctx))
    assert a.content == "first"
    assert b.content == "second"

def test_mock_raises_on_empty_script():
    mock = MockLLM(script=[])
    ctx = ConversationContext(system="", memories=[], history=[], task="")
    import asyncio
    with pytest.raises(IndexError):
        asyncio.get_event_loop().run_until_complete(mock.complete(ctx))

def test_mock_records_call_count():
    resp = LLMResponse(content="x", tool_calls=[], finish_reason="stop")
    mock = MockLLM(script=[resp, resp, resp])
    ctx = ConversationContext(system="", memories=[], history=[], task="")
    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(mock.complete(ctx))
    loop.run_until_complete(mock.complete(ctx))
    assert mock.call_count == 2
