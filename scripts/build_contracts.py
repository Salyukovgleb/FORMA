"""Generate reviewable specification artifacts from typed contracts and registry."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from docs.contracts import models as m
from docs.contracts.registry import ROWS, TABLES, group, OPERATION_STATUS

META = "Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Состояние реализации указано для каждого метода.\n"


def dump(v):
    return json.dumps(v, ensure_ascii=False, indent=2, sort_keys=True)


def schema_name(model):
    return re.sub(r"[^a-zA-Z0-9._-]", "_", model.__name__)


def sample(s, schemas):
    if "$ref" in s:
        return sample(schemas[s["$ref"].split("/")[-1]], schemas)
    if "default" in s:
        return s["default"]
    if "const" in s:
        return s["const"]
    if "enum" in s:
        return s["enum"][0]
    if "anyOf" in s:
        return sample(s["anyOf"][0], schemas)
    t = s.get("type")
    if t == "object":
        return {k: sample(v, schemas) for k, v in s.get("properties", {}).items()}
    if t == "array":
        return []
    if t == "integer":
        return max(1, s.get("minimum", 1))
    if t == "boolean":
        return False
    if t == "null":
        return None
    if s.get("format") == "uuid":
        return "11111111-1111-4111-8111-111111111111"
    if s.get("format") == "date-time":
        return "2026-10-30T12:00:00Z"
    if "pattern" in s:
        return "a" * 64 if s["pattern"] == "^[0-9a-f]{64}$" else "user@example.org"
    return "x" * max(1, s.get("minLength", 1))


schemas = {}
for model in {c for r in ROWS for c in r[2:4] if c is not None} | {m.ErrorEnvelope}:
    if model is m.Binary:
        continue
    sch = model.model_json_schema(ref_template="#/components/schemas/{model}")
    schemas.update(sch.pop("$defs", {}))
    schemas[schema_name(model)] = sch
spec = {
    "openapi": "3.1.0",
    "info": {
        "title": "FORMA planned API",
        "version": "0.1.0-draft",
        "description": "Design contract; no implemented routes.",
    },
    "paths": {},
    "components": {
        "schemas": schemas,
        "securitySchemes": {
            "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
            "refreshCookie": {"type": "apiKey", "in": "cookie", "name": "forma_refresh"},
        },
    },
}
registry = []
docs = {}
catalog = []
for i, (method, path, req, res, status, role, task, uc, effect) in enumerate(ROWS, 1):
    aid = f"API-{i:03}"
    tag = group(path)
    oid = re.sub(r"(?<!^)(?=[A-Z])", "_", uc).lower()
    params = []
    for key in re.findall(r"{(.*?)}", path):
        sch = (
            {"type": "integer", "minimum": 1}
            if key == "revision"
            else {
                "type": "string",
                **({"maxLength": 80} if key == "template_id" else {"format": "uuid"}),
            }
        )
        params.append({"name": key, "in": "path", "required": True, "schema": sch})
    if res and schema_name(res).startswith("Page_"):
        params += [
            {
                "name": "limit",
                "in": "query",
                "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
            },
            {"name": "cursor", "in": "query", "schema": {"type": "string", "maxLength": 2048}},
        ]
    if uc == "ListProjects":
        params += [
            {"name": "q", "in": "query", "schema": {"type": "string", "maxLength": 200}},
            {
                "name": "status",
                "in": "query",
                "schema": {"type": "string", "enum": ["active", "deleted"], "default": "active"},
            },
        ]
    if uc == "DeleteNode":
        params += [
            {
                "name": "expected_revision",
                "in": "query",
                "required": True,
                "schema": {"type": "integer", "minimum": 1},
            },
            {"name": "recursive", "in": "query", "schema": {"type": "boolean", "default": False}},
        ]
    if status == 202 and uc != "CancelJob":
        params.append(
            {
                "name": "Idempotency-Key",
                "in": "header",
                "required": True,
                "schema": {"type": "string", "minLength": 16, "maxLength": 128},
            }
        )
    if role == "refresh" or uc == "Login":
        params.append(
            {
                "name": "Origin",
                "in": "header",
                "required": True,
                "schema": {"type": "string", "maxLength": 2048},
            }
        )
    if role == "refresh":
        params.append(
            {
                "name": "X-CSRF-Token",
                "in": "header",
                "required": True,
                "schema": {"type": "string", "minLength": 32, "maxLength": 128},
            }
        )
    headers = {
        "X-Request-ID": {
            "schema": {"type": "string", "format": "uuid"},
            "description": "Server correlation id",
        },
        "Cache-Control": {
            "schema": {"type": "string", "const": "no-store"},
            "description": "No shared caching",
        },
    }
    if uc in ["Login", "RotateSession"]:
        headers["Set-Cookie"] = {
            "schema": {"type": "string"},
            "description": "forma_refresh; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth; Max-Age=remaining session lifetime",
        }
    response = {"description": "Успешный ответ", "headers": headers}
    if res:
        if res is m.Binary:
            response["content"] = {
                t: {"schema": {"type": "string", "format": "binary"}}
                for t in [
                    "application/octet-stream",
                    "application/pdf",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "application/zip",
                    "text/plain",
                    "image/png",
                    "image/jpeg",
                ]
            }
            headers["Content-Disposition"] = {
                "schema": {"type": "string"},
                "description": "attachment; filename ASCII fallback; filename*=UTF-8; PDF inline only with disposition=inline",
            }
            params.append(
                {
                    "name": "disposition",
                    "in": "query",
                    "schema": {
                        "type": "string",
                        "enum": ["attachment", "inline"],
                        "default": "attachment",
                    },
                }
            )
        else:
            response["content"] = {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{schema_name(res)}"},
                    "example": sample(schemas[schema_name(res)], schemas),
                }
            }
    errors = [400, 422, 429, 500, 503]
    if role != "public":
        errors += [401, 403, 404]
    if method != "GET":
        errors += [409]
    if req:
        errors += [413, 415]
    if uc in ["ReadContent", "RestoreFileRevision"]:
        errors += [415]
    if uc in ["RestoreProject", "DownloadArtifact"]:
        errors += [410]
    responses = {str(status): response}
    for e in sorted(set(errors)):
        responses[str(e)] = {
            "description": f"HTTP {e}; see error catalog",
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/ErrorEnvelope"}}
            },
        }
    operation = {
        "operationId": oid,
        "tags": [tag],
        "summary": uc,
        "description": effect,
        "x-endpoint-id": aid,
        "x-status": OPERATION_STATUS.get(oid, "planned"),
        "x-acl": role,
        "parameters": params,
        "responses": responses,
        "security": []
        if role == "public"
        else [{"refreshCookie": []}]
        if role == "refresh"
        else [{"bearerAuth": []}],
    }
    if req:
        operation["requestBody"] = {
            "required": True,
            "content": {
                ("multipart/form-data" if req is m.Upload else "application/json"): {
                    "schema": {"$ref": f"#/components/schemas/{schema_name(req)}"},
                    **(
                        {}
                        if req is m.Upload
                        else {"example": sample(schemas[schema_name(req)], schemas)}
                    ),
                }
            },
        }
    spec["paths"].setdefault(path, {})[method.lower()] = operation
    tests = [f"{prefix}-{i:03}" for prefix in ["UNIT-API", "API", "INT-API", "SEC-API"]]
    implementation_status = OPERATION_STATUS.get(oid, "planned")
    record = {
        "implementation_status": implementation_status,
        "id": aid,
        "method": method,
        "path": path,
        "operation_id": oid,
        "group": tag,
        "request": schema_name(req) if req else None,
        "response": schema_name(res) if res else None,
        "status": status,
        "acl": role,
        "task": f"BE-{task:03}",
        "tables": {
            "RegisterUser": ["users", "rate_limit_buckets"],
            "Login": ["users", "auth_sessions", "rate_limit_buckets"],
            "RotateSession": [
                "users",
                "auth_sessions",
                "used_refresh_tokens",
                "rate_limit_buckets",
            ],
            "Logout": ["users", "auth_sessions", "used_refresh_tokens"],
            "LogoutAll": ["users", "auth_sessions"],
            "ListSessions": ["users", "auth_sessions"],
            "RevokeSession": ["users", "auth_sessions"],
        }.get(uc, TABLES[tag]),
        "tests": tests,
        "effect": effect,
    }
    registry.append(record)

    def fields(model):
        if model is None:
            return "Тело отсутствует."
        if model is m.Binary:
            return "Поток bytes; не JSON. MIME определяется сохранёнными метаданными и whitelist."
        s = schemas[schema_name(model)]
        out = ["| Поле | JSON schema | Обязательное |", "|---|---|---|"]
        for k, v in s.get("properties", {}).items():
            out.append(
                f"| `{k}` | `{json.dumps(v, ensure_ascii=False)}` | {k in s.get('required', [])} |"
            )
        return "\n".join(out) + "\n\nПример:\n```json\n" + dump(sample(s, schemas)) + "\n```"

    section = f"""\n## {aid} — {uc}

`{method} {path}` · {implementation_status} · operationId `{oid}` · tag `{tag}`.

Назначение и транзакция: {effect}

Авторизация: `{role}`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
{dump(params)}
```

Запрос — `{schema_name(req) if req else "none"}`:

{fields(req)}

Успех HTTP {status} — `{schema_name(res) if res else "none"}`:

{fields(res)}

Ошибки: {", ".join(map(str, sorted(set(errors))))}; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: {", ".join(record["tables"]) or "нет"}; planned BE-046 audit будет добавлять event `{oid}`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `{tests[0]}` — правило use case; `{tests[1]}` — happy path и DTO;
`{tests[2]}` — транзакция/rollback и конфликт; `{tests[3]}` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-{task:03}](../tasks/TASK-BE-{task:03}.md),
[ADR-0001](../adr/0001-modular-monolith.md).
"""
    docs[tag] = docs.get(tag, "# API: " + tag + "\n\n" + META) + section
    catalog.append(
        f"| {aid} | `{method} {path}` | {schema_name(req) if req else '—'} → {schema_name(res) if res else '204'} | {role} | BE-{task:03} |"
    )
for tag, body in docs.items():
    (ROOT / f"docs/api/{tag}.md").write_text(body)
(ROOT / "docs/contracts/openapi.json").write_text(dump(spec) + "\n")
(ROOT / "docs/contracts/endpoints.json").write_text(dump(registry) + "\n")
(ROOT / "docs/09_API_ENDPOINT_CATALOG.md").write_text(
    "# Каталог API\n\n"
    + META
    + f"\nВсего **{len(ROWS)}** методов: 9 implemented (health/identity), 37 planned. Базовый префикс /api/v1, health без него.\n\n| ID | Метод | DTO | ACL | Задача |\n|---|---|---|---|---|\n"
    + "\n".join(catalog)
    + "\n\nПолные спецификации: "
    + ", ".join(f"[{t}](api/{t}.md)" for t in docs)
    + ".\n\n[OpenAPI](contracts/openapi.json) · [Pydantic](contracts/models.py) · [реестр связей](contracts/endpoints.json).\n"
)
for name, model in [("project", m.Project), ("job", m.Job), ("errors", m.ErrorEnvelope)]:
    (ROOT / f"docs/examples/sample-{name}.json").write_text(
        dump(sample(schemas[schema_name(model)], schemas)) + "\n"
    )
print(f"Generated {len(ROWS)} endpoints, {len(schemas)} schemas")
