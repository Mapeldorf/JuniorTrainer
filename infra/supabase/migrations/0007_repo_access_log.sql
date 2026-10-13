-- JuniorTrainer — acceso-repo-github-tool (tarea 1.1)
-- Registro de auditoria de cada acceso a un repositorio de GitHub durante
-- una generacion (ver openspec/changes/acceso-repo-github-tool,
-- specs/github-repo-access/spec.md: "Registro de auditoria de cada
-- acceso"). Solo lo escribe y lee FastAPI con service_role, igual que
-- generation/exercise; se habilita RLS por consistencia con el resto del
-- esquema (0001_schema.sql), pero sin policies: ningun cliente anon o
-- authenticated necesita verla.

create table public.repo_access_log (
  id uuid primary key default gen_random_uuid(),
  generation_id uuid not null references public.generation (id),
  tech_lead_id uuid not null references public.profile (id),
  "owner" text not null,
  repo text not null,
  commit_sha text,
  result text not null check (result in ('ok', 'error')),
  created_at timestamptz not null default now()
);

comment on table public.repo_access_log is 'Auditoria de cada acceso a un repositorio de GitHub durante una generacion: quien, que repo, que commit, y si tuvo exito.';

create index repo_access_log_generation_id_idx on public.repo_access_log (generation_id);

alter table public.repo_access_log enable row level security;
