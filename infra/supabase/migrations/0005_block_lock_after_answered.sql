-- JuniorTrainer — bloques-asignaciones (tarea 1.1)
-- Un bloque con alguna respuesta ya registrada en cualquiera de sus
-- asignaciones se vuelve inmutable (nombre y composicion), igual que ya
-- son inmutables exercise (al guardarse), assignment_exercise y answer.
-- Ver design.md - Decisions (openspec/changes/bloques-asignaciones).

create or replace function public.block_has_answers(p_block_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.assignment a
    join public.answer an on an.assignment_id = a.id
    where a.block_id = p_block_id
  );
$$;

-- block: solo bloquea el campo que cambia (name); deleted_at sigue libre,
-- igual que exercise_lock_after_saved con deleted_at en exercise.
create or replace function public.block_lock_after_answered()
returns trigger
language plpgsql
as $$
begin
  if new.name is distinct from old.name and public.block_has_answers(old.id) then
    raise exception 'block % ya tiene respuestas: no se puede editar el nombre', old.id;
  end if;
  return new;
end;
$$;

create trigger block_lock_after_answered_trg
  before update on public.block
  for each row execute function public.block_lock_after_answered();

-- block_exercise: bloquea anadir o quitar ejercicios de un bloque ya resuelto.
create or replace function public.block_exercise_lock_after_answered()
returns trigger
language plpgsql
as $$
declare
  target_block_id uuid;
begin
  if tg_op = 'DELETE' then
    target_block_id := old.block_id;
  else
    target_block_id := new.block_id;
  end if;

  if public.block_has_answers(target_block_id) then
    raise exception 'block % ya tiene respuestas: no se puede cambiar su composicion', target_block_id;
  end if;

  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

create trigger block_exercise_lock_after_answered_trg
  before insert or delete on public.block_exercise
  for each row execute function public.block_exercise_lock_after_answered();

-- search_path fijo, mismo patron que 0002_harden_functions.sql.
alter function public.block_has_answers(uuid) set search_path = public;
alter function public.block_lock_after_answered() set search_path = public;
alter function public.block_exercise_lock_after_answered() set search_path = public;
