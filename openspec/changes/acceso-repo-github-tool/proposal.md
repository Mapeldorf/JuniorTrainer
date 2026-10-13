# Proposal

## Why

La especificación del proyecto (sección de generación de ejercicios) prevé que el repositorio se aporte como ZIP o como clonado local (`git clone --depth 1` a un volumen compartido), pero esa preparación nunca llegó a implementarse en código: el agente de código ya existe y lee de un `repo_path` local que, hasta ahora, se asumía ya preparado por fuera del sistema. Además, el proyecto va a acceder a repositorios **corporativos privados**, no solo públicos, lo que ese planteamiento original no contemplaba y que cambia el modelo de riesgo (credenciales, confidencialidad, superficie de red). Antes de construir la preparación local de repos, conviene fijar el enfoque definitivo: que el agente de código acceda al contenido directamente contra la API de GitHub, sin descargar ni almacenar el repositorio en ninguna máquina de la aplicación.

## What Changes

- **BREAKING**: se elimina la opción de aportar el repositorio como ZIP. Deja de estar soportada.
- **BREAKING**: se elimina el clonado local (`git clone`) y cualquier volumen compartido en disco entre el backend y el agente de código. El repositorio nunca se descarga ni se almacena en las máquinas de la aplicación.
- **BREAKING**: el campo de entrada del repositorio pasa de una ruta local / URL libre (`repo_path`) a una referencia estructurada `owner/repo` (texto), validada con una expresión estricta antes de usarse.
- El agente de código deja de leer un `repo_path` de filesystem y pasa a usar una tool que llama a la API de GitHub (listar el árbol de ficheros y leer el contenido de un fichero/blob), bajo demanda, sin paso previo de "preparar el repo".
- Autenticación contra GitHub mediante una **GitHub App** instalada solo en los repos corporativos necesarios, con permiso de solo lectura sobre contenido; la clave privada vive en el gestor de secretos del backend, nunca en texto plano. Se sustituye así cualquier dependencia de un token personal o de alcance amplio.
- Mitigación de SSRF: la tool nunca acepta una URL completa del usuario; construye la URL real contra un host fijo de configuración (`api.github.com`), valida `owner`/`repo` con una expresión estricta, y no sigue redirecciones fuera de ese host.
- Al iniciar una generación con repositorio se fija el `commit_sha` (HEAD en ese momento) una sola vez; toda la generación lee ese mismo commit, para que el contenido no cambie a mitad de proceso.
- El contenido leído del repositorio se inserta en el prompt del agente de código siempre delimitado explícitamente como datos, con una instrucción fija en el system prompt para ignorar cualquier texto dentro de código o comentarios que parezca dirigido al propio modelo (mitigación de inyección de prompt).
- Se añade un registro de auditoría (`repo_access_log`) de cada acceso a un repositorio: generación, tech lead, `owner/repo`, commit, resultado.
- La tool usa la API de árbol recursivo de Git (una sola llamada para listar todo el árbol) en vez de recorrer carpetas una a una, para minimizar peticiones contra el límite de tasa de la API de GitHub.

No cambia: las tecnologías siguen siendo obligatorias y el repositorio opcional; el agente web y el agente de código siguen lanzándose en paralelo vía A2A; el agente de ejercicios sigue recibiendo los resultados combinados de ambos en una sola llamada; el tipo (`knowledge`/`debug`/`both`) sigue determinando la forma del ejercicio, no la fuente; la regla de que sin repositorio solo se puede pedir `knowledge` sigue aplicando; la orquestación sigue como tarea de fondo de FastAPI sin cola ni worker (fuera de alcance de este cambio).

Riesgos aceptados explícitamente por el propietario del proyecto, sin mitigación en este cambio: que código de repositorios privados pueda quedar visible en ejercicios para alumnos junior de otros equipos, y que un secreto filtrado en ese código termine en un ejercicio.

## Capabilities

### New Capabilities
- `github-repo-access`: cómo el sistema localiza, autentica y lee el contenido de un repositorio de GitHub (público o corporativo privado) para alimentar la generación de ejercicios, sin descargarlo ni almacenarlo: forma de la referencia de entrada, autenticación de la aplicación, fijación de commit, límites de lectura, protección frente a SSRF, y registro de auditoría de cada acceso.

### Modified Capabilities
Ninguna. El comportamiento observable de `agent-memory` ("no relee el mismo repositorio para las mismas tecnologías") no cambia; solo cambia, como detalle de implementación, cómo se calcula la identidad del repositorio (ver `design.md`).

## Impact

- **`agents/code/app/tools/filesystem.py`**: se sustituye por una tool que llama a la API de GitHub (listar árbol, leer blob) en vez de leer el filesystem local; cambia el contrato de `list_files`/`read_file`.
- **`agents/code/app/memory.py`**: `_repo_identity` deja de invocar `git` por subprocess; la identidad del repo pasa a ser `owner/repo@commit_sha`, recibida como entrada en vez de calculada localmente.
- **`agents/code/app/input.py`, `app/service.py`, `app/executor.py`**: el contrato A2A de entrada cambia de `repo_path` a `owner`/`repo`/`commit_sha`; los prompts de `_pick_files`/`_analyze` incorporan la instrucción de ignorar texto dirigido al modelo dentro del código leído.
- **`backend/app/schemas/generation.py`**: `repo_path: str | None` se sustituye por un campo validado de referencia `owner/repo`.
- **`backend/app/orchestrator.py`**: pasa a resolver el `commit_sha` una vez por generación (vía la nueva tool/cliente de GitHub) antes de llamar al agente de código, y a escribir el registro de auditoría.
- **Backend, nueva dependencia**: cliente de autenticación de GitHub App (JWT + intercambio por token de instalación) y cliente HTTP contra `api.github.com`.
- **Infraestructura de secretos**: nueva credencial a gestionar (clave privada de la GitHub App).
- **Base de datos**: nueva tabla `repo_access_log` (migración nueva).
- **`docker-compose.yml`**: no se añade ningún volumen compartido de repos (el `Non-Goal` de preparación local del change `generacion-ejercicios-agentes` queda definitivamente descartado en lugar de pendiente).
