-- JuniorTrainer — catalogo-tecnologias (tarea 1.1)
-- Catalogo canonico de tecnologias seleccionables en la generacion de
-- ejercicios (ver openspec/changes/catalogo-tecnologias,
-- specs/technology-catalog/spec.md). Sustituye el texto libre por un
-- conjunto de nombres canonicos estables, de modo que las caches de
-- memoria de los agentes (que indexan por el nombre normalizado de las
-- tecnologias) reutilicen resultados entre generaciones.

create table public.technology (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamptz not null default now(),
  constraint technology_name_not_blank check (btrim(name) <> '')
);

comment on table public.technology is 'Catalogo canonico de tecnologias seleccionables en la generacion de ejercicios; solo lectura para clientes, se gestiona por migraciones/servicio.';

alter table public.technology enable row level security;

-- Solo lectura para usuarios autenticados; la escritura queda reservada al
-- service_role (migraciones y backend), sin policies de insert/update/delete.
create policy technology_select_authenticated on public.technology
  for select to authenticated using (true);

-- Seed inicial: 10 tecnologias relacionadas con Angular (design.md D2).
-- Idempotente: on conflict (name) do nothing.
insert into public.technology (name) values
  ('Angular'),
  ('TypeScript'),
  ('RxJS'),
  ('NgRx'),
  ('Angular Material'),
  ('Angular CDK'),
  ('Angular Router'),
  ('Angular Forms'),
  ('Angular CLI'),
  ('Jasmine')
on conflict (name) do nothing;