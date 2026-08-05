import pytest
from pathlib import Path
import tempfile
from harness.memory import MemoryStore, Memory

def test_save_and_retrieve():
    with tempfile.TemporaryDirectory() as td:
        store = MemoryStore(Path(td) / "memory.json")
        store.save_decision(task="write tests", decision="used pytest", rationale="standard tool")
        results = store.retrieve_relevant("write tests")
        assert len(results) == 1
        assert "pytest" in results[0].decision

def test_retrieve_no_match():
    with tempfile.TemporaryDirectory() as td:
        store = MemoryStore(Path(td) / "memory.json")
        store.save_decision(task="write tests", decision="used pytest", rationale="standard")
        results = store.retrieve_relevant("deploy server")
        assert len(results) == 0

def test_build_context():
    with tempfile.TemporaryDirectory() as td:
        store = MemoryStore(Path(td) / "memory.json")
        store.save_decision(task="write function", decision="used python", rationale="best practice")
        ctx = store.build_context(task="write function")
        assert ctx.task == "write function"
        assert len(ctx.memories) == 1

def test_persistence():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "memory.json"
        store1 = MemoryStore(path)
        store1.save_decision(task="task1", decision="dec1", rationale="r1")
        store2 = MemoryStore(path)
        results = store2.retrieve_relevant("task1")
        assert len(results) == 1
