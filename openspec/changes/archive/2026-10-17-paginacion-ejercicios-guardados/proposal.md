# Proposal

## Why

La pantalla `/ejercicios` carga hoy de una sola vez todos los ejercicios guardados, sin límite: a medida que el catálogo crece, la tabla se vuelve larga de recorrer y la petición trae filas que el tech lead no está mirando. Paginar en el servidor acota la carga y hace navegable el listado.

## What Changes

- El endpoint `GET /exercises` acepta paginación opcional (`page`, `page_size`) y devuelve, además de los ejercicios, el total de coincidencias para calcular el número de páginas.
- Se mantiene compatible el uso actual sin paginación (composición de bloques): si no se indica `page_size`, se devuelven todos los ejercicios coincidentes, como hasta ahora.
- **BREAKING (interno)**: la respuesta de `GET /exercises` pasa de un array plano a un objeto `{ items, total, page, page_size }`; se actualizan sus dos consumidores (la pantalla `/ejercicios` y la de edición de bloques).
- La pantalla `/ejercicios` muestra 10 ejercicios por página y añade un control de paginación numerado con Anterior/Siguiente, elegido entre los componentes Tailwind disponibles (patrón "Pagination" de Tailwind UI), construido con utilidades del tema oscuro existente.
- Cambiar el filtro o el texto de búsqueda vuelve a la página 1 y recarga el listado paginado.

## Capabilities

### New Capabilities
<!-- Ninguna: la paginación es parte del comportamiento del catálogo de ejercicios. -->

### Modified Capabilities
- `exercise-catalog`: el requisito "Listar y buscar ejercicios definitivos" pasa a exigir paginación del listado (con total de coincidencias) y un comportamiento explícito de página fuera de rango.

## Impact

- Backend: `backend/app/routers/exercises.py` (`GET /exercises`), `backend/app/schemas/exercise.py` (nuevo esquema de página), y el script de verificación `backend/scripts/verify_ejercicios_tech_lead.py`.
- Frontend: `generations-api.model.ts` y `generations-api.service.ts` (contrato y `listSaved`), un nuevo componente de paginación reutilizable en `core/`, y `tech-lead/ejercicios/ejercicios.{ts,html}` con sus tests; adaptación de `tech-lead/bloque-editar/bloque-editar.ts` al nuevo contrato.
- Sin cambios de base de datos ni migraciones.