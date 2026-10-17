# Proposal

## Why

El campo "Tecnologías a evaluar" del formulario de generación es hoy texto libre: el tech lead escribe cualquier cadena y el sistema la acepta. Esto produce variantes de la misma tecnología ("Angular", "angular 17", "Angular.js") que, como las cachés de memoria de los agentes indexan por el nombre normalizado de las tecnologías (`agents/web/app/memory.py`, `agents/code/app/memory.py`), rompen el reuso de memoria entre generaciones. Un catálogo canónico de tecnologías hace determinista la selección y aumenta los aciertos de caché, que es justo lo que se quiere aprovechar.

## What Changes

- Nueva tabla `public.technology` (catálogo canónico) sembrada con 10 tecnologías relacionadas con Angular, mediante la migración `0009_technology_catalog.sql`.
- Nuevo endpoint `GET /technologies` (solo tech lead) que devuelve el catálogo para poblar el formulario.
- `POST /generations` pasa a validar que cada tecnología pertenece al catálogo (comparación normalizada al nombre canónico); rechaza cualquier valor fuera del catálogo.
- El formulario de generación sustituye el input de texto libre y su botón "Añadir" por un selector de múltiples tecnologías desplegable y con búsqueda, poblado desde el catálogo.
- Sin cambios en el agente validador (`technology-validation`) ni en cómo se guardan las tecnologías: `generation.technologies` sigue almacenando los nombres canónicos, para no romper la caché ni los consumidores existentes (`exercise-catalog`, listados).
- **Fuera de alcance** (futuras propuestas): gestionar el catálogo (alta/edición/borrado de tecnologías desde la app) y hacer que el agente validador valide las tecnologías introducidas por el tech lead antes de guardarlas.

## Capabilities

### New Capabilities
- `technology-catalog`: catálogo canónico de tecnologías seleccionables en el sistema y su consulta de solo lectura por parte del tech lead.

### Modified Capabilities
- `exercise-generation`: la entrada de tecnologías de una generación deja de ser texto libre y pasa a ser una selección determinista desde el catálogo, validada por el backend contra él.

## Impact

- Base de datos: nueva migración `infra/supabase/migrations/0009_technology_catalog.sql` (tabla `technology` + seed de 10 filas).
- Backend: nuevo `backend/app/routers/technologies.py` y `backend/app/schemas/technology.py`; registro del router en `backend/app/main.py`; validación contra el catálogo en `backend/app/routers/generations.py` (y su script de verificación).
- Frontend: nuevo componente `frontend/src/app/core/technology-multiselect/`; `getTechnologies()` en `frontend/src/app/core/generations-api.service.ts` y su modelo; adaptación de `frontend/src/app/tech-lead/generar/generar.{ts,html}`.
- Tests: vitest del multiselect, del servicio de API y de la pantalla de generación.