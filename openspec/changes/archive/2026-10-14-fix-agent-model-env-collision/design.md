# Design

## Context

Ver `proposal.md` para la causa raiz confirmada. Patron identico en los 5 agentes, verificado por inspeccion de cada `config.py`/`llm.py`:

| Agente | Campo `Settings` | Variable colisionada | Usado en |
|---|---|---|---|
| web, code, exercises | `generator_model: str = "generator"` | `GENERATOR_MODEL` | `llm.py`: `model=settings.generator_model` |
| evaluator | `evaluator_model: str = "evaluator"` | `EVALUATOR_MODEL` | `llm.py`: `model=settings.evaluator_model` |
| reviewer | `reviewer_model: str = "reviewer"` | `REVIEWER_MODEL` | `llm.py`: `model=settings.reviewer_model` |

Ninguno de estos campos se referencia desde ningun otro sitio (`service.py` solo llama a `build_*_model()`, nunca lee el campo directamente) -- confirmado con `grep -rn "generator_model\|evaluator_model\|reviewer_model" agents/*/app/*.py agents/*/scripts/*.py`.

`docker-compose.yml` pasa `env_file: .env` a los 5 servicios de agentes y al de `litellm` por igual; no hay forma de que un agente reciba `.env` sin recibir tambien las variables que son solo de `litellm`.

## Goals / Non-Goals

**Goals:**
- Eliminar la clase de bug, no solo el caso detectado: que ninguna variable de entorno que exista para `infra/litellm/config.yaml` pueda volver a colarse por accidente en el `Settings` de un agente.
- Cambio minimo: no tocar `docker-compose.yml` ni separar `.env` por servicio, que seria una reestructuracion mucho mayor para un problema que tiene una solucion mas simple.

**Non-Goals:**
- No se separa `.env` en un fichero por servicio ni se deja de pasar `env_file: .env` a todos los servicios: seria una propuesta de infraestructura aparte, con su propio coste/beneficio, y no hace falta para cerrar este bug.
- No se renombran `GENERATOR_MODEL`/`EVALUATOR_MODEL`/`REVIEWER_MODEL` a algo mas especifico de LiteLLM (p. ej. `LITELLM_GENERATOR_MODEL`): seguiria siendo valido y mas simple seria eliminar la lectura por parte del agente, que es la mitad de la colision que no necesita existir.

## Decisions

- **Eliminar los campos `Settings.*_model` y usar constantes de modulo en cada `llm.py`, en vez de renombrarlos para evitar la colision.** Es la recomendacion pedida: renombrar (p. ej. `agent_generator_model_name`) solo parchea el sintoma de esta colision concreta y dejaria el campo seguir siendo un `Settings` leido de variable de entorno -- la misma clase de bug podria repetirse con cualquier variable futura que coincida de nombre entre `infra/litellm/config.yaml` y algun `config.py` de agente. Estos valores nunca han sido realmente "configuracion" en el sentido que el resto de `Settings` lo es (URLs, credenciales, timeouts que si varian por entorno): son el alias logico fijo que el protocolo interno del proyecto usa para hablar con LiteLLM, igual de fijo que el nombre de un endpoint. Sacarlos de `Settings` y ponerlos como constante en `llm.py` (junto al codigo que los usa) lo deja imposible de romper por una variable de entorno, sea cual sea su nombre.
- **Una constante de modulo simple (`_MODEL_NAME = "generator"`), no un `Enum` ni una funcion.** No hay mas de un valor posible por agente ni logica alrededor; una constante de string es lo mas simple que resuelve el problema.
- **No se añade un test automatizado que falle si alguien reintroduce el campo en `Settings`.** Se descarta por ahora: el equipo de este proyecto es el propio usuario, y la tabla de este `design.md` mas el requirement nuevo en la spec ya documentan por que no debe volver a aparecer; un test dedicado seria sobre-ingenieria para un problema que, una vez corregido y documentado, es de bajo riesgo de repetirse exactamente igual.

## Risks / Trade-offs

- [Si en el futuro alguien necesita de verdad que el modelo logico sea configurable por entorno (p. ej. para pruebas A/B), esta decision lo hace mas dificil de añadir luego] → Mitigacion: no hay ningun caso de uso real hoy que lo necesite (los 3 modelos logicos estan fijados por diseño en `infra/litellm/config.yaml` desde `litellm-virtual-keys`); si apareciera esa necesidad, volver a añadir el campo a `Settings` con un nombre que no colisione (p. ej. `agent_generator_model_override`) es un cambio trivial cuando haga falta, no una decision que cueste revertir.
- [Este fix no se puede verificar con un test unitario rapido sin levantar LiteLLM de verdad, porque el bug solo se manifiesta por la combinacion real de variables de entorno del contenedor] → Mitigacion: la verificacion manual descrita en tasks.md reproduce las condiciones reales (contenedor con `env_file: .env` completo) en vez de mockear el entorno, que es precisamente como se detecto el bug originalmente.
