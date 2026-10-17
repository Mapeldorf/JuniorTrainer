# Tasks

## 1. Base de datos: catálogo de tecnologías

- [x] 1.1 Crear `infra/supabase/migrations/0009_technology_catalog.sql`: tabla `public.technology (id, name unique not null, created_at)`, RLS activada, política de `select` para autenticados (sin políticas de escritura) y seed idempotente de las 10 tecnologías Angular (design.md D1/D2); aplicarla y verificar con una consulta que la tabla tiene 10 filas y `relrowsecurity = true`.
- [x] 1.2 Verificar la política: una consulta anónima no devuelve filas y una autenticada sí, y no existe ninguna política de `insert`/`update`/`delete` sobre `technology`.

## 2. Backend: endpoint de consulta del catálogo

- [x] 2.1 Crear `backend/app/schemas/technology.py` (`Technology {id, name}`) y `backend/app/routers/technologies.py` con `GET /technologies` (`require_tech_lead`) que devuelve el catálogo, registrándolo en `backend/app/main.py`; verificar que devuelve las 10 tecnologías y que un usuario `student` recibe 403.
- [x] 2.2 Extender `backend/scripts/verify_ejercicios_tech_lead.py` (o el script de verificación equivalente) para cubrir `GET /technologies`: lista completa para tech lead y 403 para alumno; verificarlo ejecutando el script.

## 3. Backend: validación de tecnologías contra el catálogo

- [x] 3.1 En `backend/app/routers/generations.py`, antes de crear la generación, canonicalizar cada tecnología contra el catálogo (trim + comparación sin distinguir mayúsculas) y rechazar con `422` si alguna no pertenece al catálogo (design.md D4); verificar con peticiones de tecnología válida, fuera de catálogo (422) y variante de mayúsculas/espacios (aceptada y guardada con el nombre canónico).
- [x] 3.2 Añadir al script de verificación el caso de rechazo: comprobar que una petición con una tecnología fuera del catálogo responde `422` y no crea ninguna fila de `generation`; verificarlo ejecutando el script.

## 4. Frontend: servicio de API del catálogo

- [x] 4.1 Añadir el modelo `Technology {id, name}` a `frontend/src/app/core/generations-api.model.ts` y `getTechnologies(): Observable<Technology[]>` a `frontend/src/app/core/generations-api.service.ts` (`GET /technologies`); verificar con un test en `generations-api.service.spec.ts` que emite la petición a la URL correcta.

## 5. Frontend: componente `technology-multiselect`

- [x] 5.1 Crear el componente standalone `frontend/src/app/core/technology-multiselect/` (design.md D5): trigger con chips de las seleccionadas + placeholder, panel desplegable con buscador y checkboxes del catálogo, roles ARIA (`combobox`/`listbox`/`option`, `aria-expanded`), navegación con flechas/Enter/Escape, cierre al hacer clic fuera y estados de carga/error/vacío; verificarlo con `npm test` (compila y se renderiza).
- [x] 5.2 Añadir `technology-multiselect.spec.ts` con tests de: seleccionar/deseleccionar una tecnología, filtrar por el buscador, seleccionar con teclado, cerrar con Escape y mostrar el estado vacío/error; verificar con `npm test`.

## 6. Frontend: integración en el formulario de generación

- [x] 6.1 Adaptar `frontend/src/app/tech-lead/generar/generar.ts`: cargar el catálogo al iniciar (con estado de carga/error), sustituir `newTechnology`/`addTechnology`/`removeTechnology` por la selección del multiselect y hacer que `isValid()` dependa de esa selección; verificar con `npm test`.
- [x] 6.2 Sustituir en `generar.html` el input de texto libre y su botón "Añadir" por `<app-technology-multiselect>`, mostrando el error de carga del catálogo si falla; verificar que no queda ningún campo de texto libre de tecnologías.
- [x] 6.3 Actualizar `generar.spec.ts`: no se puede generar sin selección, se envían los nombres canónicos seleccionados y un fallo al cargar el catálogo se muestra sin romper la pantalla; verificar con `npm test`.

## 7. Verificación de integración

- [x] 7.1 Ejecutar `npm test` y `npm run build` en `frontend/`, y `openspec validate --change catalogo-tecnologias --strict`; confirmar que todo pasa.
- [ ] 7.2 Con la app levantada, comprobar de punta a punta que el formulario solo permite seleccionar del catálogo (con búsqueda), que genera con las tecnologías seleccionadas y que una generación repetida con las mismas tecnologías produce un acierto de memoria en la traza de Langfuse.

## Workflow follow-up

- Archivar el change cuando la implementación esté completa: `openspec archive catalogo-tecnologias` (sincroniza `technology-catalog` y `exercise-generation`) y merge del PR de archivado contra `develop`.