# Design

## Context

Ver `proposal.md` - Why. Restricciones de la especificacion del TFM (artifact "AIDebugger: especificacion del proyecto"): autenticacion en Supabase Auth con JWT, sin autorregistro, `service_role` solo en FastAPI (seccion 2 y 11), ocho tablas con borrado logico salvo `block_exercise` (seccion 8), FastAPI + LiteLLM + frontend en `docker-compose.yml`, base de datos y auth fuera de Compose (seccion 11).

## Goals / Non-Goals

**Goals:**
- Dejar un esqueleto que corra de verdad (migraciones aplicadas, backend que arranca, imagenes que construyen) antes de construir generaciones y agentes.
- Que la autorizacion por rol no dependa solo de FastAPI: las reglas criticas (quien lee que, que filas son inmutables) viven tambien en RLS y triggers de Postgres.

**Non-Goals:**
- Generaciones, bloques, asignaciones, respuestas y agentes (pasos 2 y 3 del plan de trabajo).
- Pantallas del frontend mas alla de login, alta de contrasena y recuperacion.
- Despliegue a Digital Ocean (solo CI de lint/build en este cambio).

## Decisions

**Nombres de tabla en snake_case, no PascalCase.** La seccion 8 de la especificacion nombra las tablas en PascalCase (`Profile`, `BlockExercise`...). Postgres pliega los identificadores sin comillas a minusculas, asi que usar PascalCase sin comillas habria creado tablas en minusculas de todas formas pero con un desajuste engañoso entre el SQL escrito y el nombre real. Se usa snake_case (`profile`, `block_exercise`...), la convencion idiomatica de Postgres/Supabase; el mapeo 1:1 con la especificacion se deja anotado en el proposal.

**Validacion del JWT via `GET /auth/v1/user`, no verificacion local de la firma.** Alternativa considerada: verificar la firma en local con JWKS (`PyJWT` + `PyJWKClient`). Se descarta por ahora porque Supabase esta migrando de secreto compartido HS256 a claves asimetricas por proyecto, y verificar en local ata el backend al algoritmo de firma vigente y a la rotacion de claves. Delegar en el endpoint de Supabase Auth (lo que hace `auth.get_user()` del SDK) es mas lento (una llamada de red por peticion) pero correcto pase lo que pase con el algoritmo. Si el volumen de peticiones lo justifica mas adelante, se puede cambiar a JWKS local sin tocar la spec `user-auth` (es un detalle de implementacion).

**RLS como segunda capa, no como unica capa.** `service_role` vive solo en FastAPI (seccion 11), que es quien hace la mayoria de las escrituras y por tanto puede saltarse RLS. Aun asi se define RLS completo por rol en las 8 tablas: es la capa que protege los datos si alguna vez una clave `anon`/`authenticated` llega a consultar Supabase directamente (hoy no ocurre, pero no depender de que el equipo lo recuerde siempre es mas seguro), y dobla como documentacion ejecutable de "el esquema y los roles" que pide el paso 1 del plan de trabajo.

**El store de OpenSpec vive en este mismo repositorio, no en uno aparte.** La seccion 12 de la especificacion original describe un store de OpenSpec en su propio repositorio de Git, pensado para compartir especificaciones entre varios repos de codigo. Decision explicita del usuario para este proyecto: un unico repositorio (`Mapeldorf/JuniorTrainer`) sirve de codigo y de store, usando `openspec init` en modo "repo-local" en vez de `openspec store setup`. Pendiente: actualizar la seccion 12 del documento de especificacion para que no contradiga esto.

**`docker-compose.yml` de este cambio solo trae `frontend`, `backend` y `litellm`.** Los cinco agentes (seccion 11) se añaden en el paso 2, cuando existan; añadirlos ahora como servicios vacios no aporta nada comprobable.

## Risks / Trade-offs

- [Validar el JWT contra la red en cada peticion añade latencia y un punto de fallo externo] → Si se vuelve un cuello de botella, migrar a verificacion JWKS local; no cambia el contrato de `user-auth`, solo la implementacion de `get_current_profile`.
- [Los triggers de inmutabilidad (`exercise_lock_after_saved`, `reject_update`) son la unica barrera para esas reglas ahora mismo, ya que `service_role` también los atraviesa si el backend tiene un bug] → Cubrir estas reglas con tests de integracion contra Supabase antes del paso 3, cuando el backend empiece a escribir `answer` y `assignment_exercise` de verdad.
- [snake_case diverge del nombre literal de la especificacion] → Documentado en el proposal y en este design; cualquiera que lea el SQL junto a la especificacion puede hacer el mapeo sin ambiguedad.
- [La configuracion de Supabase Auth (Site URL, Redirect URLs permitidas para `redirect_to` en invitaciones y recuperacion) se gestiona a mano en el dashboard; no esta versionada como las migraciones de esquema] → Supabase CLI permite expresar `site_url` y `additional_redirect_urls` en `supabase/config.toml` y aplicarlos con `supabase config push`, igual que el esquema. Pendiente de evaluar como un change futuro si se quiere trazabilidad completa tambien sobre la configuracion de Auth, no solo sobre el SQL.

## Migration Plan

Las migraciones `0001_schema.sql` y `0002_harden_functions.sql` ya estan aplicadas al proyecto de Supabase `uwgqxdfpkkbenmynwlmk` (no hay entorno previo que migrar: es el primer esquema). Quedan versionadas en `infra/supabase/migrations/` para que cualquier otro entorno (o una recreacion del proyecto) parta del mismo estado con `supabase db push` o `apply_migration`.
