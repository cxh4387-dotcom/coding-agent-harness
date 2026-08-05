import json
import uuid
from datetime import datetime
from pathlib import Path
from harness.models import ConversationContext, Memory

class MemoryStore:
    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._memories: list[Memory] = self._load()

    def _load(self) -> list[Memory]:
        if self.store_path.exists():
            data = json.loads(self.store_path.read_text(encoding="utf-8"))
            return [Memory(**m) for m in data]
        return []

    def _save(self):
        data = [m.__dict__ for m in self._memories]
        self.store_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def save_decision(self, task: str, decision: str, rationale: str):
        mem = Memory(
            id=str(uuid.uuid4()),
            task=task,
            decision=decision,
            rationale=rationale,
            timestamp=datetime.now().isoformat(),
            tags=task.lower().split(),
        )
        self._memories.append(mem)
        self._save()

    def retrieve_relevant(self, task: str) -> list[Memory]:
        keywords = set(task.lower().split())
        return [m for m in self._memories if keywords & set(m.tags)]

    def build_context(self, task: str) -> ConversationContext:
        relevant = self.retrieve_relevant(task)
        memories = [f"Past decision for '{m.task}': {m.decision} ({m.rationale})" for m in relevant]
        return ConversationContext(
            system="You are a coding agent. Write code, run tests, and fix failures.",
            memories=memories,
            history=[],
            task=task,
        )
