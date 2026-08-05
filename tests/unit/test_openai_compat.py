import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from harness.llm.openai_compat import OpenAICompatibleLLM
from harness.models import ConversationContext, LLMResponse, ToolCall

def test_openai_compat_initializes():
    llm = OpenAICompatibleLLM(base_url="http://localhost:8080/v1", api_key="sk-test", model="gpt-4")
    assert llm.base_url == "http://localhost:8080/v1"
    assert llm.model == "gpt-4"

@pytest.mark.asyncio
async def test_openai_compat_parses_response():
    llm = OpenAICompatibleLLM(base_url="http://localhost:8080/v1", api_key="sk-test", model="gpt-4")
    mock_response = {
        "choices": [{
            "message": {
                "content": "I will write a file",
                "tool_calls": [{
                    "id": "call_1",
                    "function": {"name": "write_file", "arguments": '{"path": "a.py", "content": "print(1)"}'}
                }]
            },
            "finish_reason": "tool_calls"
        }]
    }
    with patch.object(llm, '_raw_call', new_callable=AsyncMock, return_value=mock_response):
        ctx = ConversationContext(system="sys", memories=[], history=[], task="write a file")
        result = await llm.complete(ctx)
        assert result.finish_reason == "tool_calls"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "write_file"
        assert result.tool_calls[0].arguments["path"] == "a.py"

@pytest.mark.asyncio
async def test_openai_compat_no_tool_calls():
    llm = OpenAICompatibleLLM(base_url="http://localhost:8080/v1", api_key="sk-test", model="gpt-4")
    mock_response = {
        "choices": [{
            "message": {"content": "Done!", "tool_calls": None},
            "finish_reason": "stop"
        }]
    }
    with patch.object(llm, '_raw_call', new_callable=AsyncMock, return_value=mock_response):
        ctx = ConversationContext(system="", memories=[], history=[], task="")
        result = await llm.complete(ctx)
        assert result.finish_reason == "stop"
        assert len(result.tool_calls) == 0
        assert result.content == "Done!"
