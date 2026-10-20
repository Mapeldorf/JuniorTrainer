# Design

## Context

Hoy `agents/validator` es un agente sin estado: `app/service.py` hace una unica llamada al modelo logico `validator` (con un reintento correctivo si la respuesta no cumple el esquema) para decidir si cada entrada es una tecnologia de programacion, con politica default-deny. No tiene ninguna conexion a base de datos.

El backend ya hace, antes de llamar al validador, una comprobacion de duplicado exacto case-insensitive (`ilike` sin comodines contra `public.technology`, ver `backend/app/routers/technologies.py`). Esa comprobacion se queda igual: esta propuesta añade una segunda comprobacion, semantica, dentro del validador.

El proyecto ya tiene un patron establecido para dar a un agente acceso de solo lectura a una tabla de `public` con un rol Postgres dedicado y sin privilegios de escritura: `agents_exercise_reader` (`infra/supabase/migrations/0003_agents_memory.sql`, consumido por `agents/exercises/app/db.py` y `agents/exercises/app/tools/saved_exercises.py`). Esta propuesta sigue el mismo patron para el validador.

Ver proposal.md - Why para la motivacion completa.

## Goals / Non-Goals

**Goals:**
- El validador detecta cuando una entrada ya esta cubierta semanticamente por una tecnologia existente del catalogo, aunque el nombre no coincida de forma exacta.
- El acceso a base de datos del validador es de solo lectura, sobre una unica tabla, con credenciales propias y separadas de las de cualquier otro agente o rol.
- Un fallo de esa consulta se comporta igual que cualquier otro fallo del validador: fatal para la tarea (fail-closed), sin excepciones.

**Non-Goals:**
- No se toca la comprobacion exacta que ya hace el backend en el alta (`ilike`): sigue siendo la primera instancia, sin cambios.
- No se añade una herramienta de escritura: el validador nunca crea, actualiza ni borra tecnologias del catalogo.
- No se resuelve aqui si una generacion en curso con un nombre no canonico (p. ej. una generacion antigua, anterior a este change) debe re-mapearse a un nombre canonico con efecto retroactivo; esta propuesta solo decide la entrada en el momento de validarla.
- No se introduce un bucle de function-calling/tool-use dentro del modelo: la consulta al catalogo es una unica lectura determinista hecha por el codigo del agente antes de invocar al modelo, no una herramienta que el modelo decida invocar.

## Decisions

### D1: La consulta al catalogo es una lectura previa, no una tool-call del modelo
`validate_technologies` hace, antes de construir el prompt, una unica consulta que trae el catalogo completo (`id` no, solo `name`) via el nuevo `app/tools/technology_catalog.py`, y lo inserta como lista en el mensaje de usuario. El modelo decide la comparacion semantica con ese contexto, en la misma llamada (y el mismo reintento correctivo) que ya decide si cada entrada es una tecnologia de programacion.

Alternativa descartada: dar al modelo una tool de busqueda que el mismo invoque (patron agentic de function-calling). Se descarta porque el catalogo es una lista acotada (nombres de tecnologias, no un corpus grande), traerla entera es mas simple y mas barato que una ronda adicional de tool-calling, y mantiene el contrato actual de "una sola llamada con un reintento" (`service.py`), sin aumentar la superficie de fallo ni la latencia con una ronda de ida y vuelta adicional del modelo.

### D2: Nuevo rol de base de datos de solo lectura, dedicado, sobre `public.technology`
Nueva migracion de Supabase que crea `agents_validator_reader` (nombre por analogia con `agents_exercise_reader`): sin acceso al esquema `memory`, sin `USAGE` heredado de `public` salvo el `GRANT` explicito que necesita, y `GRANT SELECT` unicamente sobre `public.technology`. Nueva contraseña propia (`AGENTS_VALIDATOR_READER_PASSWORD` en `.env`), nunca compartida con otro rol.

Alternativa descartada: reutilizar la `service_role` de Supabase que ya usa el backend. Se descarta porque es la credencial con mas privilegios del sistema (lectura y escritura de todo `public`), y filtrarla desde un agente comprometido tendria un impacto mucho mayor que filtrar una credencial de solo `SELECT` sobre una sola tabla — mismo razonamiento que ya siguio `agents_exercise_reader` frente a usar `agents_memory` o `service_role`.

### D3: Conexion directa con `psycopg`, mismo patron que `agents/exercises/app/db.py`
`agents/validator/app/db.py` expone una unica funcion `conn_string()` para el rol `agents_validator_reader`, construida igual que las de `agents/exercises/app/db.py` y `agents/code/app/db.py` (usuario `rol.<project_ref>`, host/puerto/DB de `Settings`, `sslmode=require`). `app/tools/technology_catalog.py` abre una conexion `psycopg.AsyncConnection`, hace un `SELECT name FROM public.technology ORDER BY name` y cierra, una vez por tarea.

No hace falta un `SearchBudget` como el del agente de ejercicios: aqui hay como maximo una consulta por tarea (el catalogo completo en una sola query), no una serie de llamadas que un presupuesto deba acotar.

### D4: Extension del esquema de salida con `duplicate_technologies`
`_RESPONSE_FORMAT` (JSON schema estricto) añade un campo `duplicate_technologies`: array de objetos `{"input": string, "matches": string}` (`input` es la entrada introducida, `matches` el nombre canonico del catalogo con el que coincide). `ValidationResult` (`app/models.py`) añade el campo correspondiente.

Se aplica la misma coherencia defensiva que ya existe para `invalid_technologies`: si el modelo devuelve `valid=true` junto con `duplicate_technologies` no vacio, el validador trata el veredicto como `valid=false` (contradiccion, nunca se interpreta como afirmativo).

El prompt (`_SYSTEM_PROMPT`) se extiende para incluir el catalogo completo como dato (no instruccion, mismo tratamiento anti-prompt-injection que ya se da a la lista de tecnologias) y para explicar el criterio de coincidencia semantica (sinonimos, variantes de capitalizacion/espaciado ya cubiertas por el backend pero sin coste adicional si el modelo las reconoce igual, abreviaturas y nombres parciales claramente referidos a la misma tecnologia) exigiendo default-deny: ante la duda de si es o no la misma tecnologia, NO se marca como duplicado (evita falsos positivos que bloqueen tecnologias legitimamente distintas).

### D5: El backend distingue el motivo "duplicado" del motivo "no es una tecnologia"
`ValidationResult` expone si el rechazo viene de `duplicate_technologies` no vacio. En el alta (`POST /technologies`), `backend/app/routers/technologies.py` usa esa distincion para devolver 409 (Conflict) cuando el rechazo es por duplicado semantico, igual que ya devuelve 409 para el duplicado exacto, en vez del 422 que devuelve para una entrada que no es una tecnologia de programacion. En la generacion (`orchestrator.py`), no cambia nada: cualquier veredicto negativo del validador, sea por el motivo que sea, ya marca la generacion como fallida con el `reason` del validador como mensaje.

## Risks / Trade-offs

- **[Riesgo] Falso positivo semantico** (el modelo marca como duplicado dos tecnologias que en realidad son distintas, p. ej. "Angular" vs "AngularJS" si en algun momento se considerasen tecnologias separadas en el catalogo) **→ Mitigacion**: el prompt exige default-deny especificamente para la deteccion de duplicados (ante la duda, NO es un duplicado), simetrico al default-deny que ya se exige para "es una tecnologia de programacion"; el motivo (`matches`) se devuelve siempre junto al rechazo para que el tech lead pueda corregir el catalogo si el emparejamiento es incorrecto.
- **[Riesgo] El catalogo crece y encarece cada llamada** (el prompt incluye el catalogo completo en cada validacion) **→ Mitigacion**: el catalogo es una lista de nombres cortos pensada para mostrarse entera en un selector de formulario (`technology-catalog` spec), no un dataset grande; si llega a crecer mucho, es un ajuste de prompt/formato de lista, no un cambio de arquitectura.
- **[Riesgo] Nueva dependencia de infraestructura** (el validador ahora depende de que Supabase este disponible, cuando antes solo dependia de LiteLLM) **→ Mitigacion**: se acepta explicitamente como fail-closed (ver proposal.md y la spec delta de `technology-validation`): un fallo de esa consulta falla la tarea del validador igual que cualquier otro fallo, consistente con el resto del comportamiento ya fail-closed del agente; no se añade una ruta de fail-open que lo contradiga.
- **[Trade-off] Alcance tambien en generacion, no solo en el alta**: una generacion que use un nombre no canonico ya cubierto por el catalogo (p. ej. "Angular" cuando el catalogo tiene "Angular Framework") fallara igual que si fuera una tecnologia invalida, aunque la generacion no esta creando una fila del catalogo. Se acepta a proposito (pedido explicito del usuario): refuerza el uso del nombre canonico, que es precisamente la clave de cache que usa la memoria de los agentes (`specs/agent-memory/spec.md`), evitando que variantes del mismo nombre fragmenten esa cache sin que nadie lo note.

## Migration Plan

1. Nueva migracion Supabase (`infra/supabase/migrations/000N_agents_validator_reader.sql`) que crea el rol `agents_validator_reader` con `GRANT SELECT` solo sobre `public.technology`, mismo patron que `0003_agents_memory.sql` para `agents_exercise_reader`.
2. Aprovisionar la contraseña del nuevo rol (`.env.example` + entorno real), nunca hardcodeada en la migracion (mismo patron de placeholder que ya usa `0003_agents_memory.sql`).
3. Desplegar el codigo del agente validador (nuevo `db.py`, `tools/technology_catalog.py`, cambios en `service.py`/`models.py`) junto con la migracion; el agente no arranca sin la nueva variable de entorno de conexion, asi que no hay una ventana en la que intente usar la tool sin credenciales.
4. Sin cambios en el contrato A2A de entrada del validador (sigue aceptando la misma lista de tecnologias); el cambio es solo en su logica interna y en el campo nuevo de la salida, asi que no hace falta coordinar versiones entre backend y agente mas alla de desplegar ambos lados del campo `duplicate_technologies`/409 juntos.
5. Rollback: revertir el despliegue del agente a la version anterior (sin la tool) y, si es necesario, una migracion de bajada que revoca el acceso y elimina el rol `agents_validator_reader`; no hay datos nuevos que migrar hacia atras (el catalogo no cambia de forma, solo se le añade un nuevo lector).
