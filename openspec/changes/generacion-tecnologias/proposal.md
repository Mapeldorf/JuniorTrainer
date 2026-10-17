# Proposal

## Why

El catálogo de tecnologías introducido por `catalogo-tecnologias` es de solo lectura: sus 10 tecnologías van sembradas en la migración y el tech lead solo puede seleccionarlas. Para ampliarlo sin editar SQL a mano, el tech lead necesita dar de alta nuevas tecnologías desde la aplicación, y esa alta debe pasar por el agente validador (`technology-validation`) para que solo entren tecnologías de programación y se mantenga la propiedad canónica que hace útiles las cachés de memoria de los agentes.

## What Changes

- Nuevo endpoint `POST /technologies` (solo tech lead) que da de alta una tecnología en el catálogo: normaliza el nombre, lo valida con el agente validador antes de insertarlo, y rechaza duplicados.
- Reutilización del agente validador como puerta: el backend lo invoca por A2A (misma llamada que ya usa la generación) y solo guarda la tecnología si el veredicto es afirmativo; un rechazo o un fallo del validador no guarda nada (fail-closed).
- Interfaz de alta en la app para el tech lead: un formulario para registrar una tecnología, con su estado de validación y sus errores (rechazo del validador, duplicado), y la nueva tecnología disponible para seleccionar en el formulario de generación.
- **Fuera de alcance**: edición y borrado de tecnologías del catálogo (no se incluyen en este cambio).

## Capabilities

### New Capabilities
<!-- Ninguna: el alta es parte del catálogo existente. -->

### Modified Capabilities
- `technology-catalog`: se añade el alta de tecnologías por el tech lead, validada por el agente validador antes de persistirse, además de la consulta de solo lectura ya existente.

## Impact

- Backend: `backend/app/routers/technologies.py` (nuevo `POST /technologies`), un helper para invocar al agente validador reutilizando `send_a2a_task` y `agent_validator_url` (`backend/app/a2a_client.py`, `backend/app/config.py`), y ampliación del script de verificación del catálogo.
- Frontend: `createTechnology` en `frontend/src/app/core/generations-api.service.ts` y su modelo, más la interfaz de alta en `frontend/src/app/tech-lead/` (con su servicio/tests).
- Base de datos: sin migraciones; se reutiliza la tabla `public.technology` (`name` ya es único).
- Agentes: sin cambios; el agente validador se reutiliza tal cual.