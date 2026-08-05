.PHONY: test install lint

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v --tb=short

test-unit:
	python -m pytest tests/unit/ -v --tb=short

test-integration:
	python -m pytest tests/integration/ -v --tb=short

demo:
	python -m pytest tests/demo/ -v -s

lint:
	python -m py_compile harness/**/*.py web/**/*.py
