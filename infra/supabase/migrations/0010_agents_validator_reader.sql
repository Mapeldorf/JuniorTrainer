-- JuniorTrainer — validador-duplicados-tecnologias (tarea 1.1)
-- Rol de solo lectura para el agente validador: necesita consultar el
-- catalogo completo de tecnologias (public.technology) para detectar
-- duplicados semanticos (ver openspec/changes/validador-duplicados-tecnologias,
-- design.md "D2: Nuevo rol de base de datos de solo lectura, dedicado").
--
-- Mismo patron que agents_exercise_reader (0003_agents_memory.sql): rol
-- dedicado, solo SELECT, sin credito sobre el esquema memory ni sobre
-- ninguna otra tabla de public.
--
-- La contraseña NO va hardcodeada aqui: el placeholder
-- __AGENTS_VALIDATOR_READER_PASSWORD__ se sustituye por el valor real
-- (leido de AGENTS_VALIDATOR_READER_PASSWORD en .env) en el momento de
-- aplicar esta migracion, antes de llamar a apply_migration.

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'agents_validator_reader') then
    create role agents_validator_reader with login password '__AGENTS_VALIDATOR_READER_PASSWORD__';
  else
    execute 'alter role agents_validator_reader with login password ''__AGENTS_VALIDATOR_READER_PASSWORD__''';
  end if;
end;
$$;

revoke all on schema public from agents_validator_reader;
-- USAGE sobre public es necesario para poder referenciar cualquier objeto
-- del esquema; por si solo no da acceso a nada mas sin un GRANT explicito
-- por tabla.
grant usage on schema public to agents_validator_reader;
grant select on public.technology to agents_validator_reader;

-- public.technology tiene RLS activado (0009_technology_catalog.sql) con
-- una unica policy restringida al rol `authenticated`
-- (technology_select_authenticated). agents_validator_reader no es ese
-- rol, asi que sin BYPASSRLS no veria ninguna fila a pesar del GRANT
-- SELECT anterior -- mismo problema ya diagnosticado y corregido para
-- agents_exercise_reader en 0004_agents_exercise_reader_bypassrls.sql, que
-- aqui se evita desde el alta del rol en vez de como fix posterior.
-- BYPASSRLS no concede acceso a ninguna tabla nueva: el rol sigue sin
-- poder leer nada fuera de lo que ya tiene via GRANT (solo
-- public.technology).
alter role agents_validator_reader bypassrls;

-- Nunca credito sobre memory para este rol: su unico proposito es leer el
-- catalogo de tecnologias, no tocar la memoria de los agentes.
revoke all on schema memory from agents_validator_reader;
