PYTHON ?= .venv/bin/python
.PHONY: contracts lint typecheck test openapi-check schema-check ci-local
contracts:
	$(PYTHON) scripts/build_contracts.py
lint:
	$(PYTHON) -m ruff format --check docs/contracts scripts tests
	$(PYTHON) -m ruff check docs/contracts scripts tests
typecheck:
	$(PYTHON) -m mypy
test:
	$(PYTHON) -m pytest -q
openapi-check:
	$(PYTHON) -m pytest -q tests/contracts/test_specification.py
schema-check:
	$(PYTHON) scripts/check_schema.py
ci-local: lint typecheck test schema-check
