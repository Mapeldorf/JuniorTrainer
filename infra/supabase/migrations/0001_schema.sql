-- JuniorTrainer — esquema inicial
-- 8 tablas de aplicacion (seccion 8 de la especificacion) + roles (tech_lead/student)
-- Borrado logico salvo block_exercise, que se borra fisicamente al editar un bloque.

create extension if not exists pgcrypto;

-- =========================================================================
-- profile
-- =========================================================================

create table public.profile (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null unique,
  name text not null,
  role text not null check (role in ('tech_lead', 'student')),
  created_at timestamptz not null default now(),
  constraint profile_email_lowercase check (email = lower(email))
);

comment on table public.profile is 'Nombre y rol de cada usuario; email/contrasena viven en auth.users.';

-- auth.users -> profile al confirmar el alta (invitacion o carga inicial).
-- name y role llegan en user_metadata al invitar/crear el usuario.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profile (id, email, name, role)
  values (
    new.id,
    lower(new.email),
    coalesce(new.raw_user_meta_data ->> 'name', split_part(new.email, '@', 1)),
    coalesce(new.raw_user_meta_data ->> 'role', 'student')
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Lee el rol del usuario autenticado sin recursion de RLS en las policies de profile.
create or replace function public.current_profile_role()
returns text
language sql
security definer
set search_path = public
stable
as $$
  select role from public.profile where id = auth.uid();
$$;

-- =========================================================================
-- generation
-- =========================================================================

create table public.generation (
  id uuid primary key default gen_random_uuid(),
  repo_name text not null default '',
  technologies text not null default '',
  kind text not null check (kind in ('knowledge', 'debug', 'both')),
  status text not null check (status in ('generating', 'ready', 'done', 'error')),
  error_message text,
  created_by uuid not null references public.profile (id),
  created_at timestamptz not null default now()
);

-- =========================================================================
-- exercise
-- =========================================================================

create table public.exercise (
  id uuid primary key default gen_random_uuid(),
  generation_id uuid not null references public.generation (id),
  type text not null check (type in ('knowledge', 'debug')),
  statement text not null,
  code jsonb not null default '[]'::jsonb,
  expected_answer text,
  saved boolean not null default false,
  created_at timestamptz not null default now(),
  deleted_at timestamptz
);

create index exercise_generation_id_idx on public.exercise (generation_id);
create index exercise_saved_idx on public.exercise (saved) where deleted_at is null;

-- Un ejercicio guardado (saved = true) es inmutable salvo deleted_at (eliminarlo de la app).
create or replace function public.exercise_lock_after_saved()
returns trigger
language plpgsql
as $$
begin
  if old.saved = true and (
    new.generation_id is distinct from old.generation_id or
    new.type is distinct from old.type or
    new.statement is distinct from old.statement or
    new.code is distinct from old.code or
    new.expected_answer is distinct from old.expected_answer or
    new.saved is distinct from old.saved
  ) then
    raise exception 'exercise % ya esta guardado: solo se puede cambiar deleted_at', old.id;
  end if;
  return new;
end;
$$;

create trigger exercise_lock_after_saved_trg
  before update on public.exercise
  for each row execute function public.exercise_lock_after_saved();

-- =========================================================================
-- block
-- =========================================================================

create table public.block (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_by uuid not null references public.profile (id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger block_set_updated_at
  before update on public.block
  for each row execute function public.set_updated_at();

-- =========================================================================
-- block_exercise (se borra fisicamente al editar el bloque; sin deleted_at)
-- =========================================================================

create table public.block_exercise (
  block_id uuid not null references public.block (id) on delete cascade,
  exercise_id uuid not null references public.exercise (id),
  position int not null check (position between 1 and 100),
  primary key (block_id, exercise_id),
  unique (block_id, position)
);

-- Solo entran en un bloque ejercicios guardados y no eliminados.
create or replace function public.block_exercise_requires_saved()
returns trigger
language plpgsql
as $$
declare
  ex_saved boolean;
  ex_deleted timestamptz;
begin
  select saved, deleted_at into ex_saved, ex_deleted
  from public.exercise where id = new.exercise_id;

  if ex_saved is not true or ex_deleted is not null then
    raise exception 'exercise % no esta guardado: no puede anadirse a un bloque', new.exercise_id;
  end if;
  return new;
end;
$$;

create trigger block_exercise_requires_saved_trg
  before insert or update on public.block_exercise
  for each row execute function public.block_exercise_requires_saved();

-- =========================================================================
-- assignment
-- =========================================================================

create table public.assignment (
  id uuid primary key default gen_random_uuid(),
  block_id uuid not null references public.block (id),
  student_id uuid not null references public.profile (id),
  block_name text not null,
  assigned_at timestamptz not null default now(),
  unique (block_id, student_id)
);

create index assignment_student_id_idx on public.assignment (student_id);

-- =========================================================================
-- assignment_exercise (copia inmutable de block_exercise al asignar)
-- =========================================================================

create table public.assignment_exercise (
  assignment_id uuid not null references public.assignment (id) on delete cascade,
  exercise_id uuid not null references public.exercise (id),
  position int not null check (position between 1 and 100),
  primary key (assignment_id, exercise_id),
  unique (assignment_id, exercise_id)
);

-- La copia no cambia una vez creada.
create or replace function public.reject_update()
returns trigger
language plpgsql
as $$
begin
  raise exception '% es de solo lectura una vez creado', tg_table_name;
end;
$$;

create trigger assignment_exercise_immutable
  before update on public.assignment_exercise
  for each row execute function public.reject_update();

-- =========================================================================
-- answer
-- =========================================================================

create table public.answer (
  id uuid primary key default gen_random_uuid(),
  assignment_id uuid not null,
  exercise_id uuid not null,
  text text not null,
  verdict text not null check (verdict in ('correct', 'incomplete', 'incorrect')),
  justification text,
  answered_at timestamptz not null default now(),
  unique (assignment_id, exercise_id),
  foreign key (assignment_id, exercise_id)
    references public.assignment_exercise (assignment_id, exercise_id)
);

create index answer_assignment_id_idx on public.answer (assignment_id);

-- Una respuesta tampoco se modifica una vez dada.
create trigger answer_immutable
  before update on public.answer
  for each row execute function public.reject_update();

-- =========================================================================
-- RLS
-- =========================================================================

alter table public.profile enable row level security;
alter table public.generation enable row level security;
alter table public.exercise enable row level security;
alter table public.block enable row level security;
alter table public.block_exercise enable row level security;
alter table public.assignment enable row level security;
alter table public.assignment_exercise enable row level security;
alter table public.answer enable row level security;

-- profile: cada uno ve el suyo; el tech lead ve todos.
create policy profile_select on public.profile
  for select using (id = auth.uid() or public.current_profile_role() = 'tech_lead');

-- generation / block / block_exercise: solo tech lead (genera y compone bloques).
create policy generation_tech_lead on public.generation
  for all using (public.current_profile_role() = 'tech_lead')
  with check (public.current_profile_role() = 'tech_lead');

create policy block_tech_lead on public.block
  for all using (public.current_profile_role() = 'tech_lead')
  with check (public.current_profile_role() = 'tech_lead');

create policy block_exercise_tech_lead on public.block_exercise
  for all using (public.current_profile_role() = 'tech_lead')
  with check (public.current_profile_role() = 'tech_lead');

-- exercise: tech lead ve y gestiona todos; el alumno ve los de su copia de asignacion.
create policy exercise_tech_lead on public.exercise
  for all using (public.current_profile_role() = 'tech_lead')
  with check (public.current_profile_role() = 'tech_lead');

create policy exercise_student_select on public.exercise
  for select using (
    exists (
      select 1
      from public.assignment_exercise ae
      join public.assignment a on a.id = ae.assignment_id
      where ae.exercise_id = exercise.id
        and a.student_id = auth.uid()
    )
  );

-- assignment: tech lead gestiona todas; el alumno ve las suyas.
create policy assignment_tech_lead on public.assignment
  for all using (public.current_profile_role() = 'tech_lead')
  with check (public.current_profile_role() = 'tech_lead');

create policy assignment_student_select on public.assignment
  for select using (student_id = auth.uid());

-- assignment_exercise: tech lead gestiona; el alumno lee la copia de sus asignaciones (sin filtrar eliminados).
create policy assignment_exercise_tech_lead on public.assignment_exercise
  for all using (public.current_profile_role() = 'tech_lead')
  with check (public.current_profile_role() = 'tech_lead');

create policy assignment_exercise_student_select on public.assignment_exercise
  for select using (
    exists (
      select 1 from public.assignment a
      where a.id = assignment_exercise.assignment_id
        and a.student_id = auth.uid()
    )
  );

-- answer: tech lead lee todas; el alumno lee y crea las suyas (no las modifica: trigger answer_immutable).
create policy answer_tech_lead_select on public.answer
  for select using (public.current_profile_role() = 'tech_lead');

create policy answer_student_select on public.answer
  for select using (
    exists (
      select 1 from public.assignment a
      where a.id = answer.assignment_id
        and a.student_id = auth.uid()
    )
  );

create policy answer_student_insert on public.answer
  for insert with check (
    exists (
      select 1 from public.assignment a
      where a.id = answer.assignment_id
        and a.student_id = auth.uid()
    )
  );
