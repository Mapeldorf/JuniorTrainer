# Design

## Context

El backend no tiene ningun logger de aplicacion configurado hoy (`grep -r "logging"` en `backend/app` no devuelve nada salvo lo que trae `langfuse`/`a2a-sdk` como dependencias). Los dos puntos a corregir (`backend/app/routers/users.py:52-57` y `backend/app/routers/assignments.py:277-284`) ya capturan la excepcion (`except ... as exc`) antes de construir el `HTTPException`; el cambio es local a esos dos `except`, no requiere tocar la logica de negocio. Ver `proposal.md` para el detalle de por que estos dos puntos y por que `GET /generations/{id}` queda fuera.

## Goals / Non-Goals

**Goals:**
- Que ningun cliente de la API (alumno o tech lead) reciba el texto de una excepcion de Supabase o de un agente en el `detail` de un error HTTP.
- Que la causa raiz siga siendo diagnosticable por quien opera el backend, vía log de servidor (y, para evaluacion, vía `answer_evaluation.error_message` que ya existe).

**Non-Goals:**
- No se introduce una dependencia de logging estructurado (p. ej. `structlog`) ni un sistema de alertas: basta el modulo `logging` estandar de Python, consistente con que el proyecto no tiene ya una convencion de logging propia.
- No se añade un exception handler global (`@app.exception_handler(Exception)`) que capture cualquier error no previsto: Starlette ya devuelve un 500 generico sin detalles para excepciones no capturadas (comportamiento por defecto con `debug=False`, que es el actual), asi que no hace falta un handler nuevo para ese caso. Esta propuesta solo corrige los dos sitios donde el codigo construye el mensaje de error explicitamente con el texto de la excepcion.
- No cambia `GET /generations/{id}` (ver proposal.md - Impact): decision de diseño ya existente y fuera de alcance.

## Decisions

- **`logging.getLogger(__name__)` por modulo, sin modulo de logging compartido nuevo.** Es el patron mas simple que cubre el requisito ("registrar en el log del servidor") sin añadir infraestructura. Alternativa descartada: crear `app/logging_config.py` con configuracion centralizada -- no hace falta para loguear dos `except` concretos, y uvicorn ya configura un handler de logging razonable por defecto (se ve en stdout).
- **Mensajes genericos fijos, no parametrizados por tipo de error.** `invite_student` siempre devuelve el mismo mensaje de conflicto (p. ej. "No se ha podido invitar al alumno"); el endpoint de evaluacion siempre devuelve el mismo mensaje de error de evaluacion. No se intenta distinguir "email ya existente" de otros errores de Supabase en el mensaje al cliente (si se necesitara distinguirlo, seria una propuesta aparte que si cambiaria el contrato de la API).
- **No tocar `answer_evaluation.error_message`.** Ya guarda el detalle completo en una tabla interna no expuesta por ningun endpoint a alumnos; sirve como mecanismo de diagnostico sin pasar por logs, asi que se mantiene tal cual.

## Risks / Trade-offs

- [Mensajes genericos dan menos contexto al tech lead o al alumno para autodiagnosticar su propio error, p. ej. "ese email ya existe"] -> Mitigacion: el log de servidor conserva el detalle completo para quien opera el backend; si en el futuro se quiere distinguir casos de uso legitimos (como email duplicado) del lado del cliente, es una decision de producto aparte, no un relajamiento de esta regla de seguridad.
- [Usar `logging` sin configuracion explicita depende de la configuracion por defecto de uvicorn para que los logs sean visibles] -> Mitigacion: ya es el comportamiento actual del resto del proyecto (ninguna parte de `backend/app` configura logging hoy), asi que no se introduce una regresion nueva.
