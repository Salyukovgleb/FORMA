# Пример взаимодействия frontend

Владелец: backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-027/037/044; [frontend contract](../22_FRONTEND_BACKEND_CONTRACT.md).

Пример планируемого API; server пока не реализован. UUID и token берутся из реальных
ответов приложения, их не следует hardcode в production.

```javascript
const saved = await fetch(`/api/v1/projects/${projectId}/files/${fileId}/content`, {
  method: "PUT",
  headers: {Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json"},
  body: JSON.stringify({content: editorText, expected_revision: contentRevision})
});
if (saved.status === 409) {
  // Preserve editorText; fetch current revision and show conflict resolution.
  showConflict(await saved.json());
} else if (!saved.ok) {
  showError(await saved.json());
} else {
  contentRevision = (await saved.json()).revision;
}
```

После сохранения получить project revision из GET tree; compilation/export принимает
expected_project_revision и Idempotency-Key. Poll GET job до terminal, затем скачать artifact
через authenticated fetch. Viewer может export, но не save/compile; трактовать 403 явно.
