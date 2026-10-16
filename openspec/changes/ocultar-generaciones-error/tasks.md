# Tasks

## 1. Backend: excluir las generaciones en error del listado

- [ ] 1.1 En `backend/app/routers/generations.py`, cambiar `list_pending_generations` para filtrar por estado `generating` o `ready` (`.in_("status", ["generating", "ready"])`) en lugar de `neq("status", "done")`; verificar que `GET /generations` sigue devolviendo `ready` y ya no devuelve `error`.
- [ ] 1.2 Actualizar el docstring de `GenerationSummary` en `backend/app/schemas/generation.py` para reflejar que el listado solo trae generaciones en curso o listas para revisar; verificar que el archivo compila (`python -c "import app.schemas.generation"` desde `backend/`).
- [ ] 1.3 Ajustar `backend/scripts/verify_ejercicios_tech_lead.py` (el caso de la tarea 1.2 del change anterior) para esperar que `GET /generations` excluya `error`, y verificar ejecutando `python -m scripts.verify_ejercicios_tech_lead` desde `backend/` hasta que pase.

## 2. Frontend: servicio de rastreo de generaciones lanzadas

- [ ] 2.1 Crear `frontend/src/app/core/generation-tracker.service.ts` (inyectable, `providedIn: 'root'`) con `add(id)`, `list()` y `remove(id)` respaldados por `sessionStorage`, degradando a memoria si `sessionStorage` no está disponible; verificar con tests unitarios nuevos en `generation-tracker.service.spec.ts` que `add`/`list`/`remove` se comportan y que un `sessionStorage` caído no lanza.
- [ ] 2.2 Documentar el servicio con un comentario de cabecera que explique que rastrea las generaciones lanzadas desde la sesión (siguiendo el patrón de comentarios de `generations-api.service.ts`); verificar que el comentario referencia el requisito "Aviso de generaciones fallidas en la interfaz".

## 3. Frontend: registrar la generación al lanzarla

- [ ] 3.1 En `frontend/src/app/tech-lead/generar/generar.ts`, inyectar `GenerationTrackerService` y registrar el `id` de la respuesta de `start()` antes de navegar a `/ejercicios`; verificar con un test en `generar.spec.ts` que un `start()` correcto llama a `tracker.add(id)`.
- [ ] 3.2 Verificar con un test en `generar.spec.ts` que un `start()` fallido no registra ninguna generación.

## 4. Frontend: aviso agregado en `/ejercicios`

- [ ] 4.1 En `frontend/src/app/tech-lead/ejercicios/ejercicios.ts`, consultar `getDetail(id)` de cada id rastreado en cada tick de polling junto a `listPending()`, detectar `error` (incrementar el recuento de fallos y dejar de rastrear), quitar los `ready` del rastreo, y mantener el polling mientras haya `generating` o ids rastreados; verificar con tests que un id rastreado que pasa a `error` produce el aviso y se deja de rastrear.
- [ ] 4.2 En `ejercicios.ts`, añadir una señal propia (p. ej. `generationFailures`) separada de la señal `error` existente, con el recuento de fallos y el texto agregado en singular/plural; verificar con tests que 1 fallo y 2 fallos generan los textos correspondientes.
- [ ] 4.3 En `ejercicios.html`, renderizar el aviso como banner `role="alert"` con el estilo `alert-error` y un botón para descartarlo; verificar con un test de render que el mensaje aparece al haber un fallo y desaparece al descartarlo.
- [ ] 4.4 Verificar con un test en `ejercicios.spec.ts` que una generación en estado `error` no se renderiza en la lista de pendientes.

## 5. Verificación de integración

- [ ] 5.1 Ejecutar la batería de tests del frontend (`npm test` desde `frontend/`) y el build/typecheck (`npm run build`) hasta que pasen.
- [ ] 5.2 Prueba manual de extremo a extremo: lanzar una generación que falle, comprobar que no aparece ninguna fila en `/ejercicios` y que el banner de error agregado se muestra; repetir con dos generaciones fallidas para ver el plural.
