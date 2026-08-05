import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from harness.guardrail.scope_fence import ScopeConfig

@dataclass
class LLMConfig:
    base_url: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096

@dataclass
class SandboxConfig:
    workdir: str
    allowed_paths: list[str] = field(default_factory=list)

@dataclass
class MemoryConfig:
    store_path: str

@dataclass
class GuardrailConfig:
    custom_rules: list = field(default_factory=list)

@dataclass
class HarnessConfig:
    llm: LLMConfig
    scope: ScopeConfig
    sandbox: SandboxConfig
    memory: MemoryConfig
    guardrail: GuardrailConfig = field(default_factory=GuardrailConfig)

class ConfigStore:
    @classmethod
    def from_yaml(cls, path: Path) -> HarnessConfig:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        scope = ScopeConfig(
            allowed_tools=set(data["scope"]["allowed_tools"]),
            max_iterations=data["scope"]["max_iterations"],
            max_file_size=data["scope"]["max_file_size"],
            forbidden_patterns=[re.compile(p) for p in data["scope"].get("forbidden_patterns", [])],
        )
        return HarnessConfig(
            llm=LLMConfig(**data["llm"]),
            scope=scope,
            sandbox=SandboxConfig(**data["sandbox"]),
            memory=MemoryConfig(**data["memory"]),
            guardrail=GuardrailConfig(custom_rules=data.get("guardrail", {}).get("custom_rules", [])),
        )
