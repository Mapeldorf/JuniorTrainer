# Tasks

## 1. Backend: endpoint `POST /technologies`

- [x] 1.1 Añadir `NewTechnologyRequest {name}` a `backend/app/schemas/technology.py` y el endpoint `POST /technologies` (tech lead) en `backend/app/routers/technologies.py`: recorta el nombre, responde 422 si queda vacío, 409 si ya existe (comparación sin distinguir mayúsculas ni espacios), llama al agente validador por A2A (`send_a2a_task` + `agent_validator_url` + `new_trace_id`), responde 422 con el motivo si rechaza y 502 si falla, e inserta y responde 201 con la tecnología creada; verificarlo con peticiones para nombre válido, duplicado, rechazo del validador y vacío.
- [x] 1.2 Extender `backend/scripts/verify_ejercicios_tech_lead.py` (o el script de verificación equivalente) para cubrir el alta: alta de una tecnología de prueba (limpiándola al final), rechazo de duplicado (409) y rechazo del validador (422); verificarlo ejecutando el script.

## 2. Frontend: servicio de API

- [x] 2.1 Añadir `createTechnology(name: string): Observable<Technology>` a `frontend/src/app/core/generations-api.service.ts` (`POST /technologies`); verificar con un test en `generations-api.service.spec.ts` que emite la petición a la URL correcta con el body `{ name }`.

## 3. Frontend: pantalla de alta de tecnologías

- [x] 3.1 Crear la pantalla `frontend/src/app/tech-lead/tecnologias/` (lista del catálogo + formulario de alta con estado de éxito/validación/duplicado), registrarla en `frontend/src/app/app.routes.ts` (`/tecnologias`, con `authGuard` y `techLeadGuard`) y añadir el enlace "Tecnologías" en `tech-lead-nav.html`; verificar con `npm test` (compila y se renderiza).
- [x] 3.2 Añadir `tecnologias.spec.ts`: el alta correcta llama a `createTechnology` y refresca la lista; un rechazo del validador muestra el motivo; un duplicado muestra el aviso; sin nombre no se envía; verificar con `npm test`.

## 4. Verificación de integración

- [x] 4.1 Ejecutar `npm test` y `npm run build` en `frontend/`, y `openspec validate generacion-tecnologias --type change --strict`; confirmar que todo pasa.
- [x] 4.2 Con la app levantada, comprobar de punta a punta que el tech lead da de alta una tecnología válida desde `/tecnologias`, que aparece disponible en el selector del formulario de generación, y que se muestran correctamente el rechazo del validador y el aviso de duplicado.

## Workflow follow-up

- Archivar el change cuando la implementación esté completa: `openspec archive generacion-tecnologias` (sincroniza `technology-catalog`) y merge del PR de archivado contra `develop`.