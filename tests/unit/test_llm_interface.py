import pytest
from harness.llm.interface import LLMInterface
from harness.models import ConversationContext, LLMResponse

def test_llm_interface_is_abstract():
    with pytest.raises(TypeError):
        LLMInterface()

def test_mock_implements_interface():
    from harness.llm.mock import MockLLM
    m = MockLLM(script=[])
    assert isinstance(m, LLMInterface)
