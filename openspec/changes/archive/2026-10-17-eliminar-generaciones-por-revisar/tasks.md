# Tasks

## 1. Base de datos: cascade de las FK hacia `generation`

- [x] 1.1 Crear `infra/supabase/migrations/0008_generation_cascade_delete.sql` que recree las FK `exercise.generation_id` y `repo_access_log.generation_id` con `on delete cascade` (drop constraint + add constraint), y aplicarla; verificar con una consulta a `information_schema` / `pg_constraint` que ambas quedan con `confdeltype = 'c'`.
- [x] 1.2 Verificar manualmente en un entorno de pruebas que borrar una fila de `generation` elimina en cascada sus `exercise` y `repo_access_log`, y que el borrado de una generacion sin candidatos tambien funciona.

## 2. Backend: endpoint `DELETE /generations/{generation_id}`

- [x] 2.1 Anadir el endpoint `DELETE /generations/{generation_id}` en `backend/app/routers/generations.py` con `require_tech_lead`: 404 si no existe, 409 si `status != 'ready'`, 409 si algun ejercicio de la generacion tiene `saved = true`, y si no `204 No Content` tras borrar la generacion (cascade a candidatos y `repo_access_log`); verificar que responde el codigo esperado en cada caso.
- [x] 2.2 Extender `backend/scripts/verify_generation_e2e.py` (o el script de verificacion de generaciones equivalente) para cubrir el borrado: eliminar una generacion `ready` y comprobar que desaparece de `GET /generations` y que sus candidatos ya no existen; rechazo 409 de una `generating`; y rechazo 409 de una `ready` con un ejercicio guardado; verificar ejecutando el script.

## 3. Frontend: servicio de API

- [x] 3.1 Anadir `deleteGeneration(generationId: string): Observable<void>` a `frontend/src/app/core/generations-api.service.ts` que haga `DELETE /generations/{id}`; verificar con un test en `generations-api.service.spec.ts` que emite la peticion `DELETE` a la URL correcta.
- [x] 3.2 Ejecutar `npm test` en `frontend/` y confirmar que la suite pasa.

## 4. Pantalla `/ejercicios`: boton "Eliminar" y confirmacion

- [x] 4.1 Anadir a `EjerciciosComponent` el metodo `eliminarGeneracion(generation)` que abre `ConfirmDialogService.confirm({ destructive: true })` con un mensaje que advierte de que se eliminan los ejercicios de esa generacion, y que al confirmar llama a `deleteGeneration` y recarga `loadPending()`, mostrando el error de la pantalla si falla; anadir `confirmarEliminarGeneracion()` como metodo sustituible en tests (mismo patron que `confirmarEliminar` de guardados).
- [x] 4.2 Mostrar en `ejercicios.html` un boton "Eliminar" a la derecha de "Revisar", solo cuando `generation.status === 'ready'`, con el estilo `text-danger` usado en la tabla de guardados y `focus-ring`.
- [x] 4.3 Anadir a `ejercicios.spec.ts` los tests: el boton aparece solo en generaciones `ready`; confirmar la eliminacion llama a `deleteGeneration(generation.id)` y recarga pendientes; cancelar no llama a la API; un fallo de la API muestra el error; verificar con `npm test`.

## 5. Verificacion de integracion

- [x] 5.1 Ejecutar `npm test` y `npm run build` en `frontend/`, y ejecutar `openspec validate --change eliminar-generaciones-por-revisar --strict`; confirmar que todo pasa.
- [ ] 5.2 Con la app levantada, comprobar de punta a punta que en `/ejercicios` cada generacion `ready` muestra "Eliminar" junto a "Revisar", que el dialogo advierte de la eliminacion, y que al confirmar la generacion desaparece del listado sin ejercicios candidatos restantes.