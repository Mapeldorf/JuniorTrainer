-- JuniorTrainer — ejercicios-con-nombre (tarea 1.1)
-- Anade `name` a exercise: un nombre corto (hasta 8 palabras, garantizado
-- por el agente de ejercicios), distinto del enunciado, usado como
-- identificador visual en listados/selectores/progreso. Ver design.md
-- (openspec/changes/ejercicios-con-nombre) - Decisions, decision 6, para
-- el orden exacto de esta migracion: el backfill de los ejercicios ya
-- guardados tiene que correr ANTES de que el trigger de inmutabilidad
-- empiece a vigilar `name`, o la propia migracion chocaria con la regla
-- que esta instalando.

-- 1. Columna nullable de entrada: no se puede poner `not null` antes de
--    rellenar las filas existentes.
alter table public.exercise add column name text;

-- 2. Backfill: primeras 8 palabras del enunciado existente, con "…" si se
--    corto. En este punto el trigger exercise_lock_after_saved() TODAVIA
--    es el de 0001_schema.sql (no compara `name`), asi que este UPDATE
--    sobre filas con saved = true no choca con la inmutabilidad que esta
--    a punto de empezar a aplicarse.
update public.exercise
set name = case
  when array_length(regexp_split_to_array(trim(statement), '\s+'), 1) > 8
    then array_to_string(
      (regexp_split_to_array(trim(statement), '\s+'))[1:8],
      ' '
    ) || '…'
  else trim(statement)
end
where name is null;

-- 3. A partir de aqui, todo ejercicio (nuevo o historico) tiene nombre.
alter table public.exercise alter column name set not null;

-- 4. Ahora si: `name` se vuelve inmutable para lo ya guardado, igual que
--    el resto de columnas de exercise.
create or replace function public.exercise_lock_after_saved()
returns trigger
language plpgsql
as $$
begin
  if old.saved = true and (
    new.generation_id is distinct from old.generation_id or
    new.type is distinct from old.type or
    new.name is distinct from old.name or
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

-- search_path fijo, mismo patron que 0002_harden_functions.sql: se
-- reaplica explicitamente tras el create or replace (mismo estilo que
-- 0005_block_lock_after_answered.sql).
alter function public.exercise_lock_after_saved() set search_path = public;
