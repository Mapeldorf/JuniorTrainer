# Tasks

## 1. Infraestructura: rol de solo lectura sobre el catalogo

- [x] 1.1 Crear `infra/supabase/migrations/000N_agents_validator_reader.sql` (mismo patron que `0003_agents_memory.sql`): rol `agents_validator_reader` con `login password` por placeholder, `revoke all on schema public from agents_validator_reader`, `grant usage on schema public`, `grant select on public.technology` y `revoke all on schema memory from agents_validator_reader`. Verificar aplicando la migracion contra un proyecto Supabase local/dev y comprobando con `\du agents_validator_reader` y `\dp public.technology` que el rol solo tiene `SELECT` sobre esa tabla.
- [x] 1.2 Añadir `AGENTS_VALIDATOR_READER_PASSWORD` a `.env.example` y al entorno real, siguiendo el mismo mecanismo de sustitucion de placeholder que ya usan `AGENTS_MEMORY_PASSWORD`/`AGENTS_EXERCISE_READER_PASSWORD` al aplicar la migracion. Verificar que el valor de `.env.example` nunca es la contraseña real (placeholder documentado, no un secreto).
- [x] 1.3 Documentar el nuevo rol en el README/comentario de infra que ya describe `agents_memory`/`agents_exercise_reader`, para que quede junto al resto del inventario de roles. Verificar leyendo el fichero actualizado.

## 2. Agente validador: acceso al catalogo

- [x] 2.1 Añadir `agents_pg_host`/`agents_pg_port`/`agents_pg_database`/`supabase_project_ref`/`agents_validator_reader_password` a `agents/validator/app/config.py` (`Settings`), mismos nombres de variable que usan `agents/exercises/app/config.py` y `agents/code/app/config.py` para su rol equivalente. Verificar que `get_settings()` carga sin error con el `.env` actualizado.
- [x] 2.2 Crear `agents/validator/app/db.py` con `conn_string()` para el rol `agents_validator_reader`, mismo formato que `agents/exercises/app/db.py`. Verificar con una conexion manual (`psycopg.connect(conn_string())`) contra el entorno de desarrollo.
- [x] 2.3 Crear `agents/validator/app/tools/technology_catalog.py` con una funcion async que devuelve la lista de nombres de `public.technology` (`SELECT name FROM public.technology ORDER BY name`), abriendo y cerrando la conexion con `conn_string()`. Verificar con un test/script manual que devuelve los nombres esperados contra una tabla de prueba.
- [x] 2.4 Extender `_RESPONSE_FORMAT` y `ValidationResult` (`app/models.py`) con el campo `duplicate_technologies` (lista de `{input, matches}`), y añadir a `_parse_result` (`app/service.py`) la validacion de tipo de ese campo y la coherencia defensiva (`valid=true` con `duplicate_technologies` no vacio se trata como `valid=false`), mismo patron que ya existe para `invalid_technologies`. Verificar con un test unitario de `_parse_result` que cubre: lista vacia, lista con una coincidencia, y la coherencia defensiva.
- [x] 2.5 Extender `_SYSTEM_PROMPT` y `validate_technologies` (`app/service.py`) para incluir el catalogo obtenido en 2.3 como bloque de datos en el mensaje de usuario (marcado igual que la lista de tecnologias: dato, nunca instruccion) y pedir al modelo que señale coincidencias semanticas con default-deny (ante la duda, no es un duplicado). Verificar con `scripts/verify_validator.py` ampliado (ver tarea 2.6) contra LiteLLM.
- [x] 2.6 Ampliar `agents/validator/scripts/verify_validator.py` con un caso que valida una tecnologia ya presente en el catalogo con otro nombre (p. ej. "Angular" con el catalogo conteniendo "Angular Framework") y comprueba que el veredicto es negativo y `duplicate_technologies` señala la coincidencia; y un caso con una tecnologia realmente nueva que comprueba que no hay falso positivo. Verificar ejecutando `python -m scripts.verify_validator` contra un entorno con LiteLLM y la base de datos de desarrollo.
- [x] 2.7 Propagar el fallo de la consulta al catalogo (2.3) como fallo fatal de la tarea del validador (sin captura que lo convierta en "sin duplicados"), coherente con el resto de fallos ya fatales en `service.py`/`executor.py`. Verificar con un test que simula una excepcion de conexion y comprueba que `validate_technologies` propaga el error en vez de devolver un veredicto afirmativo.

## 3. Backend: distinguir el motivo de rechazo

- [x] 3.1 En `backend/app/routers/technologies.py`, usar `duplicate_technologies` de la respuesta del validador para devolver 409 (con el nombre de la tecnologia existente en el detalle) en vez del 422 generico, cuando el rechazo es por duplicado semantico. Verificar con un test de integracion del endpoint que mockea esa respuesta del validador y comprueba el codigo 409 y el mensaje.
- [x] 3.2 Confirmar que `backend/app/orchestrator.py` (`_call_validator`) no necesita cambios: cualquier veredicto negativo, incluido el de duplicado semantico, ya marca la generacion como fallida con el `reason` del validador. Verificar leyendo el flujo y, si no hay cambio de codigo, dejar constancia en el PR de que se revisó explícitamente.

## 4. Documentacion y specs

- [x] 4.1 Actualizar el comentario de modulo de `agents/validator/app/service.py` (la cabecera que describe "una sola llamada... para decidir si son tecnologias de programacion") para mencionar tambien la comprobacion semantica de duplicados. Verificar leyendo el fichero actualizado.
- [x] 4.2 Ejecutar `openspec validate validador-duplicados-tecnologias --strict` y corregir cualquier aviso antes de dar la propuesta por lista para implementar.
