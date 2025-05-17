.PHONY: clean clean-pyc clean-test test install-deps

clean: clean-pyc clean-test ## Remove all build, test, and Python artifacts

clean-pyc: ## Remove Python bytecode and cache files
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete
	find . -name '*~' -delete
	find . -name '__pycache__' -exec rm -rf {} +

clean-test: ## Remove test and coverage artifacts
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/

test: clean-pyc ## Run tests with pytest
	PYTHONPATH=. pytest

test-ci: clean-pyc ## Run tests in CI environment
	PYTHONPATH=. python -m pytest 

install-deps: ## Install dependencies including test dependencies
	pip install -e '.[dev]'
	pip install -r requirements-ml.txt
	pip install numpy pydantic-settings email-validator 