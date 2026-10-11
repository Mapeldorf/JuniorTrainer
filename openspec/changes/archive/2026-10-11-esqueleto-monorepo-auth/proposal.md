# Proposal

## Why

El proyecto no tiene todavia ni base de datos ni forma de entrar en la aplicacion. Antes de poder construir generaciones, bloques o agentes (pasos 2 y 3 del plan de trabajo) hace falta el esqueleto del monorepo, el esquema de Supabase con sus roles y el unico flujo de alta que define la especificacion: sin autorregistro, el tech lead se crea con un script de carga inicial y el resto de altas son invitaciones suyas por email.

## What Changes

- Esqueleto del monorepo: `frontend/`, `backend/`, `infra/`, `.github/workflows/`, `openspec/`.
- Esquema de Supabase (PostgreSQL) con las 8 tablas de la seccion 8: `profile`, `generation`, `exercise`, `block`, `block_exercise`, `assignment`, `assignment_exercise`, `answer`.
- Row Level Security por rol (`tech_lead` / `student`) en las 8 tablas, mas los triggers que imponen las reglas de negocio que la base de datos debe comprobar por si misma: un ejercicio guardado no se edita, la copia de una asignacion no cambia, una respuesta no se modifica, y solo entran en un bloque ejercicios guardados.
- Trigger `on_auth_user_created` que crea el `profile` (nombre y rol) al confirmarse el alta en `auth.users`, leyendo `name`/`role` de los metadatos con los que se invita o se crea al usuario.
- Backend FastAPI minimo: `POST /users` (invitar alumno, solo tech lead) y la dependencia que valida el JWT de Supabase y resuelve el `profile`/rol de quien llama.
- Script de carga inicial (`backend/scripts/seed_tech_lead.py`) que crea el primer tech lead directamente en Supabase Auth (sin invitacion, con contrasena ya puesta).
- `docker-compose.yml` con `frontend`, `backend` y `litellm` (la base de datos y la autenticacion viven en Supabase, no en Compose).

## Capabilities

### New Capabilities

- `user-auth`: alta y autenticacion de usuarios. Cubre que no hay autorregistro, que el tech lead es el unico origen de altas de alumnos (invitacion por email, sin contrasena temporal), la recuperacion de contrasena, y que la sesion es un JWT de Supabase que determina el rol de cada peticion.
- `data-authorization`: el esquema de datos y las reglas que la base de datos impone por rol, independientemente de la capa de API: que puede leer o escribir un tech lead frente a un alumno, y que filas se vuelven inmutables una vez guardadas, asignadas o respondidas.

### Modified Capabilities

(ninguna: es el primer cambio del proyecto)

## Impact

- Codigo nuevo: `backend/app/**`, `backend/scripts/seed_tech_lead.py`, `infra/supabase/migrations/0001_schema.sql` y `0002_harden_functions.sql` (ya aplicadas al proyecto de Supabase `uwgqxdfpkkbenmynwlmk`), `docker-compose.yml`, `.github/workflows/ci.yml`.
- Sin impacto en capacidades existentes: es el primer cambio.
- Fuera de alcance de este cambio (quedan para los pasos 2 y 3 del plan de trabajo): agentes de generacion y valoracion, endpoints de generaciones/bloques/asignaciones/respuestas, y las pantallas del frontend mas alla de login/alta/recuperacion de contrasena.
