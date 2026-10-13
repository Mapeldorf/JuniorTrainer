# Design

## Context

Ver proposal.md ("Why") para la motivacion. Estado actual relevante:

- `public.exercise` (`infra/supabase/migrations/0001_schema.sql`) no tiene ninguna columna de nombre; `statement` es el unico texto libre que identifica a un ejercicio, y es el enunciado completo que resuelve el alumno.
- `ExerciseCandidate` (`backend/app/schemas/generation.py`) es la forma compartida de un candidato y de un ejercicio guardado (`SavedExercise = ExerciseCandidate` en `backend/app/schemas/exercise.py`); se usa tal cual en la respuesta de `GET /generations/{id}`, `POST /exercises/{id}/save`, `GET /exercises` (extendida con `SavedExerciseListItem`) y dentro de `BlockExerciseItem` (`backend/app/schemas/block.py`). Anadir un campo ahi lo propaga a todos esos sitios de una vez.
- `ExerciseProgress` (`backend/app/schemas/block.py`), en cambio, NO reutiliza `ExerciseCandidate`: declara sus propios campos `type`/`statement` porque se lee de una consulta distinta (`assignment_exercise` unido a `exercise`, solo esos dos campos) en `backend/app/routers/blocks.py` (`GET /blocks/{id}`) y `backend/app/routers/users.py` (`GET /users/{id}/assignments`). Anadir `name` ahi es un cambio en paralelo, no automatico.
- El agente de ejercicios (`agents/exercises/app/service.py`) ya tiene, desde el change `ejercicios-nivel-junior`, el patron completo para esto: una constante de limite de palabras, una funcion que detecta que textos lo superan, y un unico reintento correctivo que reenvia la respuesta anterior pidiendo acortar antes de fallar la tarea. El `_SYSTEM_PROMPT` ya pide un array JSON de objetos con campos fijos.
- El contrato A2A de ejercicios (`CandidateExercise` en `agents/exercises/app/models.py`, serializado con `dataclasses.asdict()` en `executor.py`) no tiene versionado: el orquestador (`backend/app/orchestrator.py`, `_insert_candidates`) consume los campos por nombre directamente del dict que llega. Anadir un campo ahi no rompe nada ya desplegado porque agente y backend se despliegan juntos (mismo docker-compose).
- No hay ningun check de longitud a nivel de base de datos sobre `statement` (el limite de 50 palabras del change anterior se garantiza solo en el agente); se sigue el mismo criterio para `name`.
- El trigger `exercise_lock_after_saved()` (0001_schema.sql) compara explicitamente columna por columna; anadir `name` a esa comparacion es el unico cambio de esquema que hace el nombre inmutable.
- Los ejercicios ya guardados (`saved = true`) son inmutables por ese mismo trigger: una migracion que intente darles un nombre con un `UPDATE` normal, DESPUES de que el trigger ya compare `name`, seria rechazada por el propio trigger que la migracion esta instalando.

## Goals / Non-Goals

**Goals:**

- Que `name` sea un campo propio y corto, nunca una copia truncada de `statement` en tiempo de lectura (evita decidir en cada vista cuantos caracteres cortar, y permite que el agente elija un nombre mejor que un simple prefijo).
- Que el limite de palabras del nombre sea una garantia del sistema (mismo patron que el enunciado), no una indicacion al modelo.
- Que todo ejercicio history (ya guardado antes de este change) acabe con un nombre utilizable, sin dejar ninguno en blanco en las vistas que ahora muestran `name` en vez de `statement`.
- Minimizar el numero de formas/DTOs nuevos: reutilizar `ExerciseCandidate` donde ya se reutiliza, y replicar el cambio explicitamente donde `ExerciseProgress` ya vive aparte.

**Non-Goals:**

- No se hace `name` unico ni se valida contra duplicados: dos ejercicios pueden compartir nombre, igual que pueden compartir enunciado.
- No se anade un filtro de bloques por nombre de ejercicio (`GET /blocks` no gana ese parametro); el filtro de ejercicios (`GET /exercises?q=`) ya cubre la necesidad de encontrar un ejercicio por nombre antes de componer un bloque.
- No se toca la vista del alumno (`student/ejercicio`, `student/valoracion`): ahi el enunciado es el contenido, no una etiqueta, y el alumno nunca ha visto ni vera el nombre.
- No se versiona el contrato A2A del agente de ejercicios; se asume despliegue conjunto agente+backend, igual que el resto de este monorepo.

## Decisions

### 1. El nombre es un campo nuevo, redactado por el agente en la misma llamada

El agente de ejercicios anade `name` al mismo JSON que ya devuelve `statement`/`code`/`expected_answer`, en la misma llamada al modelo `generator`. `CandidateExercise` (dataclass) y `ExerciseCandidate` (schema Pydantic) ganan el campo.

Alternativa descartada: derivar el nombre en el backend truncando `statement` a N palabras. Es mas barato, pero un enunciado de 50 palabras en forma de pregunta ("¿Que hace X cuando...?") no produce una etiqueta legible al cortarlo a ciegas; pedirselo al modelo, que ya conoce el concepto exacto del ejercicio, da un nombre mejor con coste marginal (es la misma llamada, no una nueva).

Alternativa descartada: una segunda llamada al modelo dedicada solo al nombre. Mismo argumento que ya establecio el change anterior para el enunciado: dobla la latencia contra el limite de 2 minutos por tarea sin necesidad.

### 2. Limite de 8 palabras, mismo patron de reintento que el enunciado

Se anade `_MAX_NAME_WORDS = 8` (constante de modulo, junto a `_MAX_STATEMENT_WORDS = 50` ya existente) y se reutiliza literalmente el mismo mecanismo: `_statements_over_limit` generalizada (o una funcion gemela) cuenta palabras de `name`, y si algun candidato se pasa, se repite la llamada una vez con un aviso que nombra los nombres que se pasaban. Si sigue habiendo incumplimientos tras el reintento, `ExerciseGenerationError`.

8 palabras (frente a 50 del enunciado) porque un nombre es una etiqueta para un listado, no una frase: "Validacion de un modelo Pydantic con `field_validator`" son 7 palabras y ya es mas largo de lo que hace falta para distinguir una fila de otra. El numero exacto es una constante, ajustable sin tocar el diseno si la verificacion en vivo (tasks.md) muestra que se queda corto o largo -- mismo criterio que el change anterior aplico a las 50 palabras del enunciado.

Alternativa descartada: un unico reintento conjunto que cubra enunciado Y nombre a la vez con un solo mensaje. Mezclar dos motivos de reintento en un mismo aviso complica el mensaje y el codigo sin ahorrar llamadas reales (el reintento ya es uno por intento, no por campo); se mantienen los dos chequeos (de enunciado y de nombre) independientes pero componibles en el mismo turno de reintento si ambos fallan a la vez.

### 3. El nombre vive en `ExerciseCandidate`, se replica a mano en `ExerciseProgress`

Como `ExerciseCandidate` ya es la forma compartida de candidato/guardado (ver Context), anadir `name: str` ahi cubre de golpe `GET /generations/{id}`, `POST /exercises/{id}/save`, `GET /exercises` y `BlockExerciseItem` (dentro de `BlockDetail`). `ExerciseProgress` es una consulta aparte (`type, statement` directos sobre `exercise`, sin pasar por `ExerciseCandidate`): se amplia esa misma consulta a `type, statement, name` en los dos sitios que la hacen (`routers/blocks.py` y `routers/users.py`) y se anade `name: str` al schema.

Alternativa descartada: hacer que `ExerciseProgress` herede de `ExerciseCandidate`. No comparten el resto de campos (progreso trae `answered`/`verdict`/`answer_text`/`justification`, candidato trae `code`/`expected_answer`) y forzar una relacion de herencia solo por dos campos compartidos acopla dos modelos que ya son deliberadamente independientes (el propio `ExerciseProgress` ya documenta por que no reusa `SavedExercise`).

### 4. Guardar un candidato permite editar tambien el nombre, igual que la respuesta esperada

`SaveExerciseRequest` gana `name: str | None = None`, con el mismo criterio que ya tiene `expected_answer`: si se informa, sustituye al generado antes de que el ejercicio se vuelva inmutable; si se omite, se guarda el nombre tal como lo redacto el agente. El frontend (`revisar.html`/`.ts`) anade un `<input>` de texto editable para el nombre junto al `<textarea>` de la respuesta esperada, reusando el mismo patron de `answerFor`/`setAnswer` (un `name`for`/`setName` analogo).

### 5. Busqueda de ejercicios: nombre O enunciado, sin romper el filtro existente

`GET /exercises?q=` pasa de `ilike("statement", ...)` a un `or` de PostgREST sobre `name` y `statement` (`.or_(f"name.ilike.%{q}%,statement.ilike.%{q}%")`). Es un cambio aditivo: cualquier busqueda que hoy encuentra algo por su enunciado lo sigue encontrando; ademas encuentra por nombre.

Alternativa descartada: buscar solo por nombre (ya que es el identificador visual nuevo). Se descarta porque el tech lead puede recordar una frase del enunciado y no el nombre corto que puso el agente (o que el edito hace tiempo); restringir la busqueda seria una regresion para ese caso de uso real que ya cubre `exercise-catalog`.

### 6. Migracion con backfill antes de endurecer el trigger

La migracion `0006_exercise_name.sql` sigue un orden especifico para no chocar con la propia inmutabilidad que esta instalando:

1. `alter table exercise add column name text` (nullable de entrada: no se puede poner `not null` antes de rellenar las filas existentes).
2. `UPDATE exercise SET name = <derivado de statement> WHERE name IS NULL` -- en este punto el trigger `exercise_lock_after_saved()` TODAVIA no compara `name` (sigue siendo el de 0001_schema.sql), asi que el `UPDATE` sobre filas con `saved = true` no choca con la regla de inmutabilidad que esta a punto de empezar a aplicarse.
3. `alter table exercise alter column name set not null`.
4. `create or replace function exercise_lock_after_saved()` anadiendo `new.name is distinct from old.name` a la condicion que dispara la excepcion -- a partir de aqui, y solo a partir de aqui, el nombre se vuelve inmutable para lo ya guardado.

El nombre derivado en el paso 2 es una funcion SQL simple: las primeras `_MAX_NAME_WORDS` (8) palabras de `statement`, con `…` si se corto. No pasa por el agente ni por LiteLLM (no hay nada que generar: es un dato de arranque para que ninguna vista quede con un nombre vacio, no una redaccion de calidad). El tech lead puede despues eliminar esos ejercicios y regenerar si el nombre heredado no le convence -- son inmutables como cualquier otro guardado.

Alternativa descartada: dejar `name` nullable indefinidamente y resolver el hueco en el frontend (`exercise.name ?? exercise.statement`). Vuelve a introducir el problema que origina esta propuesta (enunciados largos como identificador) para todo lo generado antes del change, y complica cada vista con una regla de fallback que la migracion puede resolver una sola vez.

## Risks / Trade-offs

- **El backfill produce nombres mediocres para ejercicios antiguos** (un corte mecanico de palabras, no una redaccion) → aceptado: son pocos (los guardados antes de este change), siguen siendo utilizables como identificador aunque no sean ideales, y el tech lead puede eliminarlos y regenerar si le molesta.
- **Mas generaciones en error por el limite duro del nombre** (igual que ya es riesgo aceptado para el enunciado) → mismo mitigante: el reintento correctivo cubre el caso normal; 8 palabras es generoso para una etiqueta.
- **Dos textos que mantener sincronizados conceptualmente** (nombre y enunciado podrian divergir de forma confusa, p. ej. nombre sobre un tema que el enunciado ya no trata si el tech lead edita solo uno al guardar) → aceptado: el tech lead revisa los dos campos en la misma pantalla de revision antes de guardar, y una vez guardado ambos son igual de inmutables.
- **Migracion de datos en produccion** (el proyecto de Supabase del TFM tiene ejercicios reales ya guardados) → mitigado por el orden descrito en la decision 6: el `UPDATE` de backfill corre antes de que el trigger conozca `name`, asi que no hay fila que la migracion no pueda rellenar.

## Migration Plan

1. Aplicar `infra/supabase/migrations/0006_exercise_name.sql` (orden interno descrito en la decision 6) contra el proyecto de Supabase.
2. Reconstruir y desplegar `agent-exercises` (prompt + limite nuevo) y `backend` (schemas/routers nuevos) juntos -- el contrato A2A no esta versionado, asi que deben ir a la vez.
3. Desplegar el frontend con las vistas actualizadas.
4. Rollback: revertir el commit de codigo (agente/backend/frontend) es seguro en cualquier momento porque `name` queda como columna adicional no usada por el codigo anterior; revertir la migracion de base de datos (columna `name` y el trigger ampliado) solo si hace falta deshacer tambien el esquema, y requeriria otra migracion que quite la columna -- no se automatiza en este change porque ninguno de los cambios anteriores del proyecto lo ha necesitado.
