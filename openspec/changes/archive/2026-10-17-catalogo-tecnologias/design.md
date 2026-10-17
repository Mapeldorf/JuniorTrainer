# Design

## Context

El formulario de generación (`frontend/src/app/tech-lead/generar/generar.{ts,html}`) recoge las tecnologías como texto libre y las envía en `StartGenerationRequest.technologies` (`backend/app/schemas/generation.py`); `POST /generations` (`backend/app/routers/generations.py`) las une con `", "` y las guarda en `generation.technologies text`. Los agentes de web y código indexan su memoria por el nombre de las tecnologías normalizado (`sorted({t.strip().lower()})`, ver `agents/web/app/memory.py` y `agents/code/app/memory.py`), así que variantes del mismo nombre no reutilizan caché. Ver proposal.md - Why para la motivación y `specs/exercise-generation/spec.md` y `specs/technology-catalog/spec.md` para los requisitos.

Estado relevante: no existe tabla de tecnologías; `generation.technologies` se consume en `GET /generations` y en el listado de ejercicios guardados (`exercise-catalog`). No hay librería de componentes en el frontend (Tailwind v4 + Angular 22; tests con vitest).

## Goals / Non-Goals

**Goals:**
- Fijar un catálogo canónico de tecnologías y una operación de solo lectura para consultarlo.
- Hacer que la entrada de tecnologías sea determinista y validada en servidor.
- Preservar las claves de caché de memoria y los consumidores actuales de `generation.technologies`.

**Non-Goals:**
- Gestionar el catálogo desde la app (alta/edición/borrado): futura propuesta.
- Que el agente validador (`technology-validation`) valide tecnologías introducidas por el tech lead antes de guardarlas: futura propuesta; el validador sigue igual.
- Cambiar cómo el agente validador decide, o tocarlo: las tecnologías de catálogo siempre pasarán su veredicto.

## Decisions

**D1 - Tabla `technology` nueva, almacenando el nombre canónico (sin tabla puente).**
`public.technology (id uuid pk, name text not null unique, created_at timestamptz)`. La generación sigue guardando los nombres en `generation.technologies text` (sinónimo de nombre canónico), de modo que la clave de caché (nombres normalizados) y los consumidores existentes no cambian. Alternativa descartada: tabla puente `generation_technology` — obligaría a joins en todo el código que lee `technologies` y cambiaría el valor que alimenta la caché, sin beneficio observable.

**D2 - Catálogo inicial con 10 tecnologías relacionadas con Angular.**
Seed en la migración: **Angular, TypeScript, RxJS, NgRx, Angular Material, Angular CDK, Angular Router, Angular Forms, Angular CLI, Jasmine**. Son nombres canónicos estables; son la referencia que citan los specs. Se siembran con `on conflict (name) do nothing` para que la migración sea idempotente.

**D3 - `GET /technologies` de solo lectura, para el tech lead.**
Devuelve `[{id, name}]` con `require_tech_lead` (403 para alumno). RLS activada en `technology` con política de `select` para autenticados y sin políticas de escritura (la escritura queda reservada al service role / migraciones). Alternativa descartada: exponer el catálogo como constante en el backend — no sería una fuente de verdad única ni consultable/administrable en el futuro.

**D4 - Validación contra el catálogo en el backend, con canonicalización.**
Al iniciar una generación, el endpoint lee los nombres del catálogo y, para cada tecnología pedida, hace *trim* y compara sin distinguir mayúsculas; si coincide, la reemplaza por el nombre canónico del catálogo. Cualquier valor sin coincidencia → `422` sin crear la generación. Se mantienen los límites actuales de `StartGenerationRequest` (nº y longitud). Alternativa descartada: validar solo en el frontend — un cliente manipulado podría enviar texto libre y romper la caché; el backend debe ser la garantía.

**D5 - Selector múltiple propio (combobox) con búsqueda, sin librería externa.**
Nuevo componente standalone `core/technology-multiselect/`: un trigger que muestra las seleccionadas como *chips* y un panel desplegable con un buscador y una lista de checkboxes del catálogo. Cubre accesibilidad (roles `combobox`/`listbox`/`option`, `aria-expanded`, navegación con flechas, Enter y Escape, cierre al hacer clic fuera y gestión de foco) y estados de carga/error/vacío. Alternativas descartadas: `<select multiple>` nativo (UX pobre, poco estilizable con Tailwind) y usar `@angular/cdk` o Material (no están instalados; añadir la dependencia solo para esto no se justifica).

## Risks / Trade-offs

- [La validación añade una lectura de BD por inicio de generación] → Aceptado: la tabla es diminuta y la operación ya crea una fila en `generation`; el coste es marginal.
- [Renombrar una tecnología del catálogo dejaría huérfanas las entradas de caché con el nombre antiguo] → Los nombres se eligen canónicos y estables; el renombrado es una preocupación de la futura gestión del catálogo, no de este cambio.
- [El catálogo se consulta en cada apertura del formulario] → Aceptado: es una lista pequeña; el fallo de la consulta deja el selector vacío con un mensaje de error, sin romper la pantalla.
- [Bloquear valores fuera del catálogo reduce la flexibilidad actual] → Es el objetivo buscado: elimina variantes que rompen la caché; ampliar el catálogo se resolverá con la futura gestión (CRUD).

## Migration Plan

- Migración `infra/supabase/migrations/0009_technology_catalog.sql`: crea `public.technology`, activa RLS y su política de `select`, y siembra las 10 filas (idempotente). No hay backfill: `generation.technologies` se queda como está.
- Despliegue: migración + backend deben ir juntos (el endpoint nuevo y la validación dependen de la tabla); el frontend depende del endpoint nuevo, así que se despliega en el mismo release.
- Rollback: revertir el endpoint y la validación (volver a aceptar texto libre) y eliminar la tabla `technology`; no hay datos que migrar de vuelta.

## Open Questions

- Ninguna que cambie el alcance, los specs o el desglose de tareas.