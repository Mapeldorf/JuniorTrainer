# JuniorTrainer

Plataforma de evaluación de código generado por IA para juniors. Backend en FastAPI,
frontend en Angular 22 + Tailwind, base de datos y autenticación en Supabase,
agentes con LangChain + LiteLLM + Langfuse (a partir del paso 2 del plan de trabajo).

La especificación completa vive en el artifact "AIDebugger: especificación del
proyecto (v0.1)"; el desarrollo sigue [OpenSpec](https://github.com/Fission-AI/OpenSpec)
en modo repo-local, con `openspec/specs/` (especificación vigente) y
`openspec/changes/` (cambios en curso y archivados) dentro de este mismo repositorio.

## Estructura

```
frontend/            Angular 22 + Tailwind
backend/              FastAPI
infra/
  supabase/migrations/  Esquema de Supabase, versionado
  litellm/config.yaml    Configuración del gateway de modelos
openspec/             Especificación y cambios (SDD)
.github/workflows/    CI
docker-compose.yml    frontend + backend + litellm (la BD y la auth viven en Supabase)
```

## Requisitos

- Node.js ≥ 22.22.3 (o ≥ 24.15.0) — lo exige Angular 22. Comprueba tu versión con `node --version`.
- Python ≥ 3.12
- Docker y Docker Compose, para levantar los tres servicios juntos
- Un proyecto de Supabase (el del TFM: `uwgqxdfpkkbenmynwlmk`)

## Configuración

```bash
cp .env.example .env
```

Rellena en `.env` al menos `SUPABASE_ANON_KEY` y `SUPABASE_SERVICE_ROLE_KEY`
(Supabase dashboard → Project Settings → API). Las variables de LiteLLM/Tavily/Langfuse
no hacen falta todavía: los agentes llegan en el paso 2 del plan de trabajo.

## Arrancar en local

### Con Docker Compose (frontend + backend + litellm)

```bash
docker compose up --build
```

- Frontend: http://localhost:4200
- Backend: http://localhost:8000 (docs en `/docs`)
- LiteLLM: http://localhost:4000

### Sin Docker, servicio a servicio

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # o exporta las variables a mano
uvicorn app.main:app --reload

# Frontend (en otra terminal)
cd frontend
npm install
npm start   # http://localhost:4200
```

## Primer arranque: crear el tech lead

No hay autorregistro. El primer usuario (tech lead) se crea con:

```bash
cd backend
source .venv/bin/activate
python -m scripts.seed_tech_lead --email tu@empresa.com --name "Tu nombre"
```

Pide la contraseña por entrada segura si no se pasa `--password`. A partir de ahí,
ese tech lead invita a los alumnos desde la aplicación (`POST /users`), que les llega
por correo (SMTP configurado en el panel de Supabase).

## Base de datos

Las migraciones de `infra/supabase/migrations/` ya están aplicadas al proyecto de
Supabase del TFM. Para aplicarlas a otro proyecto (o recrearlo desde cero):

```bash
supabase link --project-ref <project-ref>
supabase db push
```

## Desarrollo guiado por especificaciones (OpenSpec)

```bash
npx @fission-ai/openspec@latest status                 # cambios en curso
npx @fission-ai/openspec@latest show <capability> --type spec   # spec vigente de una capacidad
```

Los comandos `/opsx:propose`, `/opsx:apply` y `/opsx:archive` (configurados para
Claude Code en `.claude/commands/opsx/`) cubren el ciclo completo: proponer un
cambio, implementarlo y archivarlo actualizando `openspec/specs/`.

## Estado

Ver el plan de trabajo (sección 13 de la especificación) y
`openspec/changes/esqueleto-monorepo-auth/tasks.md` para el detalle de lo hecho
y lo pendiente del paso 1.
