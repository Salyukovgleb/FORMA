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
ci-local: lint typecheck test test-integration lock-check dependency-check schema-check

lock-check:
	$(PYTHON) scripts/check_lock.py
	$(PYTHON) scripts/check_lock.py requirements-runtime.lock
	$(PYTHON) scripts/check_lock.py requirements-build.lock

.PHONY: dev-up dev-down test-compose
dev-up:
	docker compose --env-file .env -f infra/compose.yaml -f infra/compose.dev.yaml up -d --build --wait api
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

.PHONY: test-migrations test-security dependency-check
test-migrations:
	$(PYTHON) -m pytest -q tests/integration/test_migrations.py
test-security:
	$(PYTHON) -m pytest -q tests/unit/test_config_logging.py tests/unit/test_passwords.py tests/unit/test_access_tokens.py tests/unit/test_project_policy.py tests/api/test_system.py tests/security tests/integration/test_sessions.py tests/integration/test_profiles.py tests/integration/test_auth_limits.py tests/integration/test_file_storage.py tests/integration/test_projects.py
dependency-check:
	$(PYTHON) -m pip check

.PHONY: auth-limits-cleanup
auth-limits-cleanup:
	$(PYTHON) -m forma_backend.infrastructure.identity.cleanup_limits
