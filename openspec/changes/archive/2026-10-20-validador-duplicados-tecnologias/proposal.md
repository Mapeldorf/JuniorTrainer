# Proposal

## Why

La comprobación de duplicados que hace hoy el backend (`ilike` sin comodines contra `public.technology`) solo detecta una coincidencia textual exacta salvo mayúsculas y espacios. Si el catálogo ya tiene `"Angular Framework"` y un tech lead da de alta o usa en una generación `"Angular"`, el sistema no detecta que es la misma tecnología: en el alta se crearía una fila duplicada en el catálogo, y en una generación se perdería la canonicidad del nombre que usan como clave de caché la memoria de los agentes (`specs/agent-memory/spec.md`). El agente validador, que ya es el punto de paso obligatorio para decidir si una entrada es una tecnología de programación, es el lugar natural para añadir una segunda comprobación semántica contra el catálogo completo, ya que requiere criterio (sinónimos, variantes, abreviaturas) y no una simple igualdad de cadenas.

## What Changes

- El agente validador incorpora una herramienta de solo lectura que consulta el catálogo completo de tecnologías (`public.technology`) con un rol de base de datos dedicado y de solo `SELECT`, análogo al patrón ya usado por `agents/exercises/app/tools/saved_exercises.py`.
- La llamada al modelo `validator` se extiende para que, además de decidir si cada entrada es una tecnología de programación, compare semánticamente cada entrada contra los nombres del catálogo y señale cuándo una entrada ya está cubierta por una tecnología existente con otro nombre, variante o abreviatura (p. ej. `"Angular"` contra `"Angular Framework"`).
- El esquema de salida estructurada del validador (`_RESPONSE_FORMAT` / `ValidationResult`) se amplía con la lista de coincidencias semánticas detectadas (entrada introducida + tecnología existente con la que coincide). Un veredicto afirmativo (`valid=true`) sigue exigiendo que esa lista esté vacía (mismo criterio default-deny y de coherencia defensiva que ya aplica a `invalid_technologies`).
- Esta segunda comprobación se mantiene **en segunda instancia**: el backend sigue haciendo exactamente igual que hoy su comprobación exacta case-insensitive antes de invocar al validador (primera instancia, sin cambios).
- El rechazo por duplicado semántico se propaga igual que un rechazo por tecnología inválida: en el alta (`POST /technologies`) se devuelve el motivo indicando con qué tecnología existente coincide, sin crear fila; en una generación, falla la validación previa y la generación completa queda en estado de error (mismo comportamiento fail-closed que ya define `specs/technology-validation/spec.md`).
- Un fallo al consultar el catálogo (conexión caída, tiempo excedido) se trata igual que cualquier otro fallo del validador: fatal para la tarea, nunca se interpreta como "no hay duplicados".
- Nueva credencial de base de datos de solo lectura para el agente validador (rol Postgres dedicado, sin acceso de escritura ni a otras tablas), aprovisionada igual que las credenciales existentes de los demás agentes.

## Capabilities

### New Capabilities
(ninguna; la comprobación semántica es una extensión del comportamiento ya cubierto por `technology-validation`, no un comportamiento nuevo independiente)

### Modified Capabilities
- `technology-validation`: el validador pasa a comparar también cada entrada contra el catálogo completo de tecnologías y a rechazar una entrada que ya está cubierta semánticamente por una tecnología existente, con la misma política default-deny y el mismo tratamiento fail-closed de los fallos que ya aplica a la validación de "es una tecnología de programación".
- `technology-catalog`: el rechazo de duplicados en el alta deja de basarse solo en la igualdad exacta case-insensitive; se añade el rechazo por coincidencia semántica con una tecnología existente, decidido por el validador.

## Impact

- **`agents/validator/app/`**: nuevo `db.py` (cadena de conexión del rol de solo lectura), nuevo `app/tools/technology_catalog.py` (consulta del catálogo), cambios en `service.py` (prompt, `_RESPONSE_FORMAT`, lógica de coherencia) y `models.py` (`ValidationResult`).
- **`agents/validator/app/config.py`**: nuevas variables de entorno para la cadena de conexión del rol de solo lectura.
- **Infraestructura de base de datos**: nueva migración de Supabase que crea el rol Postgres de solo lectura sobre `public.technology` y su credencial, siguiendo el patrón de `infra/supabase/migrations/0003_agents_memory.sql`.
- **`backend/app/routers/technologies.py`**: adapta el mensaje de rechazo cuando el motivo es un duplicado semántico (y considera si debe devolver 409 en vez de 422 para ese caso, a definir en design.md).
- **`backend/app/orchestrator.py`**: sin cambios de lógica (ya trata cualquier veredicto negativo del validador como fatal para la generación); solo se beneficia de que el validador ahora también puede rechazar por duplicado semántico.
- **Specs afectadas**: `openspec/specs/technology-validation/spec.md`, `openspec/specs/technology-catalog/spec.md`.
