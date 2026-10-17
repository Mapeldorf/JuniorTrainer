# Design

## Context

Tras `catalogo-tecnologias` (ya archivado), el catálogo vive en `public.technology` con `name` único y se consume por `GET /technologies` (`backend/app/routers/technologies.py`). El agente validador ya decide si unas tecnologías son de programación: el backend lo invoca por A2A en `orchestrator._call_validator` (`send_a2a_task(agent_validator_url, {"technologies": [...]}, trace_id)`), con contrato de respuesta `{valid, reason, invalid_technologies}` (ver `openspec/specs/technology-validation/spec.md`).

Ver proposal.md - Why para la motivación y `specs/technology-catalog/spec.md` para los requisitos.

## Goals / Non-Goals

**Goals:**
- Permitir el alta de tecnologías por el tech lead, reutilizando el agente validador como puerta.
- Mantener el catálogo como conjunto canónico sin duplicados.
- Exponer la gestión en una pantalla propia y disponible para probar de inmediato.

**Non-Goals:**
- Editar o borrar tecnologías del catálogo.
- Cambiar el agente validador ni sus requisitos.
- Gestionar permisos distintos del tech lead.

## Decisions

**D1 - `POST /technologies` (tech lead) que responde 201 con la tecnología creada.**
Body `{name: str}`. Responde 422 si el nombre queda vacío o el validador lo rechaza, 409 si ya existe (comparación sin distinguir mayúsculas ni espacios), 502 si el validador falla, 403 si el rol no es tech lead. Encaja con el `GET /technologies` existente y con la semántica REST.

**D2 - El agente validador se reutiliza tal cual, como puerta fail-closed.**
El alta llama a `send_a2a_task` con `{"technologies": [name]}` y exige `valid == True` para insertar. Un `valid == False` responde 422 con el `reason`; un `A2ATaskError` responde 502. No se guarda nada en ninguno de los dos casos. Alternativa descartada: validar solo formato en backend — dejaría entrar cadenas que rompen la caché y contradice el objetivo de `technology-validation`.

**D3 - Normalización: se recorta el nombre y la unicidad es case-insensitive.**
Se guarda el nombre tal como lo escribe el tech lead (recortado), porque no hay una forma determinista de "canonicalizar" el casing (`RxJS`, `iOS`, `Angular CDK` no siguen una regla). El duplicado se detecta ignorando mayúsculas y espacios sobrantes, de modo que no conviven `angular` y `Angular`. Alternativa descartada: forzar Title Case — corrompería nombres con casing propio.

**D4 - Sin migración; la unicidad se apoya también en la constraint de la tabla.**
`technology.name` ya es `unique`; la comprobación previa evita el error feo y la constraint protege ante una carrera. No se añaden columnas ni tablas.

**D5 - Pantalla propia `/tecnologias` en la navegación del tech lead.**
Nueva pantalla `tech-lead/tecnologias` con la lista del catálogo y un formulario de alta que muestra éxito, rechazo del validador o duplicado; al dar de alta, la lista se refresca en la propia pantalla. El formulario de generación ya recarga el catálogo al abrirse, así que la nueva tecnología queda seleccionable sin recargar la app. Alternativa descartada: formulario embebido en la pantalla de generación — mezcla la gestión del catálogo con la generación de ejercicios.

**D6 - `createTechnology(name)` en `GenerationsApiService`.**
Mismo servicio que ya expone `getTechnologies()`, para no crear un servicio nuevo para una sola operación del mismo recurso.

## Risks / Trade-offs

- [El validador puede rechazar una tecnología legítima y bloquear su alta] → Es el comportamiento buscado (fail-closed); la interfaz muestra el motivo. Ampliar el criterio es una decisión sobre el agente (`technology-validation`), fuera de este cambio.
- [Si el agente validador está caído no se puede dar de alta] → Aceptado: fail-closed; no se quiere un catálogo sin validar.
- [Casing inconsistente si lo escriben varios tech leads] → El duplicado case-insensitive lo evita; se conserva el casing de la primera alta.
- [Carrera entre la comprobación y el insert de dos altas simultáneas] → La constraint `unique` de la tabla rechaza la segunda; despreciable en esta app de un solo tech lead.

## Migration Plan

- Sin migración. Backend (endpoint) y frontend (pantalla) van en el mismo release.
- Rollback: quitar el endpoint, la ruta/pantalla y el método del servicio; no hay estado que revertir.

## Open Questions

- Ninguna que cambie el alcance, los specs o el desglose de tareas.