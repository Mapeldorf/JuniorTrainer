-- Esquema de memoria para los agentes de generacion (web, codigo, ejercicios)
-- y los dos roles de conexion directa a Postgres que necesitan:
--   - agents_memory: lee/escribe el esquema `memory` (langgraph-checkpoint-postgres).
--     Sin privilegios sobre `public`: una fuga de sus credenciales no expone
--     datos de alumnos ni ejercicios.
--   - agents_exercise_reader: solo SELECT sobre public.exercise, para
--     `search_saved_exercises` del agente de ejercicios. No es `service_role`
--     (esa es exclusiva de FastAPI, seccion 11 de la especificacion).
--
-- Las contrasenas NO van hardcodeadas aqui: los placeholders __AGENTS_MEMORY_PASSWORD__
-- y __AGENTS_EXERCISE_READER_PASSWORD__ se sustituyen por los valores reales
-- (leidos de las variables de entorno correspondientes, ver .env.example) en el
-- momento de aplicar esta migracion, antes de llamar a apply_migration.

-- =========================================================================
-- esquema memory
-- =========================================================================

create schema if not exists memory;

comment on schema memory is
  'Memoria larga y corta de los agentes de generacion (langgraph-checkpoint-postgres). '
  'No contiene datos de alumnos: ningun nombre, email ni respuesta.';

-- =========================================================================
-- rol agents_memory: solo el esquema memory
-- =========================================================================

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'agents_memory') then
    create role agents_memory with login password '__AGENTS_MEMORY_PASSWORD__';
  else
    execute 'alter role agents_memory with login password ''__AGENTS_MEMORY_PASSWORD__''';
  end if;
end;
$$;

-- Nada sobre public: ni siquiera USAGE sobre el esquema (necesario para
-- cualquier SELECT/INSERT), asi que de entrada no puede tocar ninguna tabla.
--
-- revoke ... from agents_memory no basta: Postgres concede USAGE sobre
-- public al pseudo-rol PUBLIC por defecto, y todo rol lo hereda de ahi salvo
-- que se revoque explicitamente de PUBLIC. anon/authenticated/service_role/
-- postgres ya tienen su propio GRANT directo (no dependen de ese valor por
-- defecto), asi que revocarlo de PUBLIC no les quita nada; solo cierra el
-- hueco por el que agents_memory lo heredaria sin haberlo pedido.
revoke usage on schema public from public;
revoke all on schema public from agents_memory;

grant usage, create on schema memory to agents_memory;

-- Las tablas propias de langgraph-checkpoint-postgres dentro de `memory` las
-- crea el paquete al arrancar cada agente (su setup()), no esta migracion;
-- por eso agents_memory necesita CREATE ademas de USAGE sobre el esquema.

-- Sin esto, el search_path por defecto de una conexion nueva ("$user",
-- public) no resuelve a nada que agents_memory pueda usar (no existe un
-- esquema "agents_memory" y no tiene acceso a "public"), y el CREATE TABLE
-- de setup() fallaria con "no schema has been selected to create in".
alter role agents_memory set search_path = memory;

-- =========================================================================
-- rol agents_exercise_reader: solo lectura de public.exercise
-- =========================================================================

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'agents_exercise_reader') then
    create role agents_exercise_reader with login password '__AGENTS_EXERCISE_READER_PASSWORD__';
  else
    execute 'alter role agents_exercise_reader with login password ''__AGENTS_EXERCISE_READER_PASSWORD__''';
  end if;
end;
$$;

revoke all on schema public from agents_exercise_reader;
-- USAGE sobre public es necesario para poder referenciar cualquier objeto del
-- esquema; por si solo no da acceso a nada mas sin un GRANT explicito por tabla.
grant usage on schema public to agents_exercise_reader;
grant select on public.exercise to agents_exercise_reader;

-- Nunca credito sobre memory para este rol: su unico proposito es leer
-- ejercicios guardados, no tocar la memoria de los agentes.
revoke all on schema memory from agents_exercise_reader;
