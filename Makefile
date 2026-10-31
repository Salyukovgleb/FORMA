PYTHON ?= .venv/bin/python
.PHONY: contracts lint typecheck test openapi-check schema-check ci-local
contracts:
	$(PYTHON) scripts/build_contracts.py
lint:
	$(PYTHON) -m ruff format --check src alembic docs/contracts scripts tests
	$(PYTHON) -m ruff check src alembic docs/contracts scripts tests
typecheck:
	$(PYTHON) -m mypy
test:
	$(PYTHON) -m pytest -q
openapi-check:
	$(PYTHON) -m pytest -q tests/contracts/test_specification.py
schema-check:
	$(PYTHON) scripts/check_schema.py
ci-local: lint typecheck test test-integration lock-check schema-check

lock-check:
	$(PYTHON) scripts/check_lock.py
	$(PYTHON) scripts/check_lock.py requirements-runtime.lock
	$(PYTHON) scripts/check_lock.py requirements-build.lock

.PHONY: dev-up dev-down test-compose
dev-up:
	docker compose --env-file .env -f infra/compose.yaml up -d --wait postgres
dev-down:
	docker compose --env-file .env -f infra/compose.yaml down
test-compose:
	$(PYTHON) scripts/check_compose.py

.PHONY: migrate migration-check test-integration
migrate:
	$(PYTHON) -m alembic upgrade head
migration-check:
	$(PYTHON) -m alembic check
test-integration:
	$(PYTHON) -m pytest -q tests/integration
