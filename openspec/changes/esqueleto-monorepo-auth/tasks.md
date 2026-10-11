# Tasks

## 1. Monorepo y OpenSpec

- [x] 1.1 Crear `frontend/`, `backend/`, `infra/`, `.github/workflows/` y verificar con `ls` que existen
- [x] 1.2 `.gitignore` para Node, Python y variables de entorno
- [x] 1.3 Inicializar OpenSpec en modo repo-local (`openspec init`) y verificar `openspec context --json` devuelve `root`

## 2. Esquema de Supabase y roles

- [x] 2.1 Escribir `infra/supabase/migrations/0001_schema.sql` con las 8 tablas, los triggers de inmutabilidad y las policies de RLS por rol
- [x] 2.2 Aplicar la migracion al proyecto `uwgqxdfpkkbenmynwlmk` y verificar con `list_tables` que las 8 tablas existen con `rls_enabled: true`
- [x] 2.3 Revisar los avisos de seguridad (`get_advisors`) y corregirlos en `0002_harden_functions.sql` (search_path fijo, EXECUTE no expuesto a `anon`); verificar que solo queda el aviso esperado de `current_profile_role`

## 3. Backend: alta y autenticacion

- [x] 3.1 `app/deps.py`: dependencia `get_current_profile` que valida el JWT contra Supabase Auth y resuelve el `profile`; `require_tech_lead` para los endpoints de solo tech lead
- [x] 3.2 `POST /users`: invita a un alumno con la Admin API (nombre + rol en los metadatos, `redirect_to` al frontend); responde 201, y 403 si quien llama no es tech lead
- [x] 3.3 `scripts/seed_tech_lead.py`: crea el primer tech lead con `create_user` (email confirmado, contrasena propia); verificar que imprime el id del usuario creado
- [x] 3.4 Verificar que el backend importa sin errores (`from app.main import app`) y que `/health` y `POST /users` aparecen en las rutas

## 4. Frontend: pantallas de autenticacion

- [x] 4.1 Scaffold Angular 22 + Tailwind en `frontend/` y verificar que `ng build` termina sin errores
- [x] 4.2 Cliente de Supabase (`@supabase/supabase-js`) configurado con la publishable key, mas un guard de ruta que exige sesion
- [x] 4.3 Pantalla Login (email + contrasena contra Supabase Auth) con su estado de error inline, siguiendo el diseno del artifact "JuniorTrainer UI" (panel partido, paleta zinc/blue-700, tipografia Geist)
- [x] 4.4 Pantalla de alta de contrasena desde el enlace de invitacion o de recuperacion (`/set-password`), que llama a `supabase.auth.updateUser({ password })` y distingue enlace invalido/caducado
- [x] 4.5 Pantalla Forgot con la confirmacion (ForgotSent) inline, mismo componente, mismo mensaje exista o no el email
- [ ] 4.6 Verificar manualmente el flujo completo: invitar a un alumno de prueba desde `POST /users`, abrir el enlace del correo, elegir contrasena y entrar (pendiente: requiere los tres servicios corriendo y acceso a un correo real; ver README)

## 5. docker-compose y CI

- [x] 5.1 `docker-compose.yml` con `frontend`, `backend` y `litellm`; variables de entorno via `.env` en la raiz
- [x] 5.2 `.env.example` con las variables que piden `app/config.py`, el frontend y LiteLLM (Supabase, redirect, modelos, Tavily, Langfuse)
- [x] 5.3 `.github/workflows/ci.yml`: build/test de `frontend/` y `backend/` filtrado por ruta (`dorny/paths-filter`), en cada PR y en push a `main`
- [ ] 5.4 Verificar `docker compose build` termina sin errores para los tres servicios (pendiente: este entorno no tiene un daemon de Docker disponible; `docker compose config` valida la sintaxis y los tres `Dockerfile` estan escritos y revisados, pero el build en si no se ha ejecutado)

## Workflow follow-up

- Archivar el cambio (`/opsx:archive`) cuando los grupos 4 y 5 esten completos y el flujo manual de la tarea 4.6 se haya probado.
- Actualizar la seccion 12 del documento de especificacion original para reflejar que el store de OpenSpec vive en este mismo repositorio (ver design.md - Decisions).
