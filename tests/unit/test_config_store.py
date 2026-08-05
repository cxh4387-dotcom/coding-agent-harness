import pytest
from pathlib import Path
import tempfile
from harness.config import ConfigStore, HarnessConfig

def test_load_default_config():
    config_path = Path(__file__).parent.parent.parent / "config" / "default.yaml"
    config = ConfigStore.from_yaml(config_path)
    assert config.llm.model == "glm-5.2"
    assert config.scope.max_iterations == 50
    assert "read_file" in config.scope.allowed_tools

def test_custom_config():
    yaml_content = """
llm:
  base_url: "http://localhost:8080/v1"
  model: "gpt-4"
  temperature: 0.5
  max_tokens: 2048
scope:
  allowed_tools: [read_file]
  max_iterations: 10
  max_file_size: 1024
  forbidden_patterns: ["rm"]
sandbox:
  workdir: "/tmp/ws"
  allowed_paths: []
memory:
  store_path: "/tmp/mem.json"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f.flush()
        config = ConfigStore.from_yaml(Path(f.name))
    assert config.llm.model == "gpt-4"
    assert config.scope.max_iterations == 10
    assert config.scope.max_file_size == 1024
