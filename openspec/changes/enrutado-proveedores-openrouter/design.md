# Design

## Context

Ver `proposal.md` seccion Why para la motivacion.

Estado de partida en `infra/litellm/config.yaml`: cinco deployments cuyo modelo se resuelve por variable de entorno (`GENERATOR_MODEL`, `EVALUATOR_MODEL`, `REVIEWER_MODEL`, `VALIDATOR_MODEL`, `JUDGE_MODEL`), todos con un modelo de OpenRouter en el `.env` desplegado, y cuatro deployments de respaldo en Hugging Face (`*-fallback-hf`). Ninguno fija politica de enrutado: OpenRouter balancea entre todos los proveedores del modelo.

Datos tomados el 2026-10-26 de la API publica de OpenRouter (`/api/v1/models/<modelo>/endpoints`, `/api/v1/endpoints/zdr` y `/api/v1/providers`, que publica la sede `headquarters` de cada proveedor):

| Modelo | Proveedores | Con ZDR | ZDR y sede en EEE o pais con adecuacion | Solo EEE |
|---|---|---|---|---|
| `deepseek/deepseek-v4.1-flash` (generator, evaluator) | 41 endpoints | 36 | 30 endpoints, 22 proveedores | Nebius (NL) |
| `z-ai/glm-5.3-flashx` (reviewer hoy) | Z.AI (SG) | Z.AI | **ninguno** | ninguno |
| `z-ai/glm-5.3-flash` (validator, reviewer nuevo) | 38 endpoints | 32 | 25 endpoints, 21 proveedores | Inceptron (SE), NextBit (ES), Nebius (NL, caido al consultar) |
| `anthropic/claude-sonnet-4.6` (judge) | 9 endpoints | 6 (Bedrock, Vertex) | 6 | ninguno (Amazon y Google tienen sede en EE. UU.) |

Comprobado en vivo contra OpenRouter y contra LiteLLM 1.106.0 (la imagen `main-latest` desplegada), con un proxy desechable sin base de datos:

- `zdr: true` y `data_collection: "deny"` **no excluyen** a Z.AI para FlashX ni a SiliconFlow (Singapur) para DeepSeek: las dos llamadas se completan.
- `extra_body: {provider: {...}}` en `litellm_params` llega a OpenRouter: una lista `only` imposible devuelve el 404 de OpenRouter citando esa lista.
- Un 404 por politica, en un alias sin fallback, llega al cliente como `litellm.NotFoundError` con el mensaje de OpenRouter (`No allowed providers are available for the selected model...`). OpenRouter no prueba otro proveedor.
- El mismo 404 en un alias **con** fallback dispara el respaldo: el cliente recibe un 200 con `x-litellm-attempted-fallbacks: 1` y `model` igual al modelo de Hugging Face. En la prueba, Hugging Face lo enruto a `baseten` (`x-inference-provider`).
- Tras el 404, LiteLLM deja el deployment primario en *cooldown* durante unos segundos: las llamadas siguientes van directas al respaldo.
- Parametros de nivel superior que envian los agentes y las evals (`metadata`, `response_format`, `reasoning`) y uno con el mismo nombre (`provider`) **no** sustituyen la politica del deployment. Una clave literal `extra_body` en el JSON de la peticion **si** la sustituye (ver Risks).

## Goals / Non-Goals

**Goals:**

- Que ninguna llamada a OpenRouter pueda acabar en un proveedor que retenga o recolecte los datos, o con sede en un pais sin decision de adecuacion.
- Que la politica sea configuracion versionada y revisable, verificada en CI, y no un ajuste de una cuenta externa.
- Que la consecuencia de la politica sobre el revisor se resuelva con un modelo de calidad ya medida.

**Non-Goals:**

- Cubrir el respaldo de Hugging Face con una politica equivalente (decision 6).
- Verificar la certificacion DPF de cada proveedor estadounidense (decision 3, riesgos).
- Garantizar la region del centro de datos: OpenRouter publica la sede del proveedor, y la lista de centros de datos solo para unos pocos.

## Decisions

### Decision 1: la politica vive en el deployment, via `extra_body.provider`

Cada deployment de OpenRouter lleva `extra_body: {provider: {...}}` en `litellm_params`. LiteLLM no tiene un parametro propio para el objeto `provider` de OpenRouter (su transformacion solo mapea `transforms`, `models` y `route`), pero reenvia `extra_body` tal cual; comprobado en 1.106.0.

**Alternativas descartadas:**

- *Ajustes de privacidad de la cuenta de OpenRouter* (ZDR por grupo de modelos y proveedores permitidos a nivel de cuenta). Tienen una ventaja real -- una peticion no puede relajarlos--, pero viven fuera del repositorio, no se revisan en un PR ni los ve el CI, y la cuenta puede compartirse con otros usos. Se dejan como defensa adicional recomendada (Risks), no como el control.
- *Que cada agente envie la preferencia en su llamada.* Seis sitios en lugar de uno, y un agente nuevo naceria sin ella. Los agentes ademas no saben a que proveedor resuelve su alias, y no deben saberlo (`litellm-agent-keys`, resolucion de modelo logico aislada).

### Decision 2: `zdr: true` y `data_collection: "deny"`, las dos

OpenRouter las trata como politicas distintas: ZDR filtra por retencion, `data_collection` por uso de los datos (entrenamiento, almacenamiento no transitorio). Se fijan las dos porque cuestan lo mismo y dejan explicita cada garantia, sin depender de que una implique la otra en la clasificacion de OpenRouter. `allow_fallbacks` se deja en su valor por defecto: dentro de la lista, que OpenRouter pruebe otro proveedor si el primero no esta disponible es lo deseable, porque todos cumplen la politica.

### Decision 3: lista cerrada `only` por jurisdiccion: EEE y paises con decision de adecuacion

ZDR y `deny` no cubren la jurisdiccion (Context). Hace falta un filtro mas. Alternativas consideradas:

| Opcion | Que deja (DeepSeek / GLM-Flash / Sonnet) | Por que si o por que no |
|---|---|---|
| (a) Sin lista, solo ZDR y `deny` | todo lo ZDR, incluidos SG | **No**: no mitiga el riesgo 11. Comprobado que Z.AI y SiliconFlow pasan. |
| (b) Solo EEE | Nebius / Inceptron, NextBit / ninguno | **No**: DeepSeek depende de un unico proveedor y el juez se queda sin ninguno. Cada caida de Nebius manda el trafico al respaldo de Hugging Face, que **no tiene politica** (decision 6): mas trafico por el camino peor. |
| (c) EEE y paises con adecuacion, EE. UU. incluido por el DPF | 22 / 21 / 2 proveedores | **Elegida.** Mitiga lo que nombra el riesgo (paises *sin* decision de adecuacion), conserva la redundancia entre proveedores y deja al juez con Bedrock y Vertex. |
| (d) `ignore` de los proveedores con sede en CN y SG | casi todo | **No**: lista negra, fail-open. Un proveedor nuevo con sede en un pais sin adecuacion recibiria trafico el dia que OpenRouter lo anadiera. |

Reglas de construccion de la lista:

- Criterio: la sede (`headquarters`) que publica `/api/v1/providers`. Paises con decision de adecuacion: Andorra, Argentina, Canada, Islas Feroe, Guernsey, Israel, Isla de Man, Japon, Jersey, Nueva Zelanda, Corea del Sur, Suiza, Reino Unido, EE. UU. (DPF) y Uruguay.
- Proveedor **sin sede publicada** (Mancer, PrimeIntellect, Makora, Reka, Relace, Near AI, Darkbloom): fuera. Ante la duda, fuera.
- La lista se limita a los proveedores que hoy sirven alguno de los cuatro modelos configurados con ZDR y cumplen el criterio, no a todos los del catalogo que lo cumplen: 25 slugs. Se usa el slug base (`deepinfra`, `google-vertex`), que cubre todas las variantes y regiones del proveedor.
- Cambiar un modelo obliga a revisar la lista: si el modelo nuevo no tiene ningun proveedor en ella, sus llamadas fallan con 404 y caen al respaldo (decision 5 y spec "Todo modelo primario tiene proveedor dentro de la politica"). El comentario de la configuracion lo dice.

**El matiz de EE. UU.** La decision de adecuacion del DPF cubre solo a las organizaciones certificadas en el Data Privacy Framework. Este change no verifica la certificacion de cada uno de los 22 proveedores con sede en EE. UU. de la lista; lo deja como riesgo residual explicito y como seguimiento. Y OpenRouter, el intermediario, tiene sede en EE. UU.: todo el trafico pasa por EE. UU. antes de llegar a cualquier proveedor, con o sin lista.

### Decision 4: el revisor pasa de `glm-5.3-flashx` a `glm-5.3-flash`

FlashX solo lo sirve Z.AI (Singapur), excluido por la decision 3: con la politica activa, el revisor fallaria siempre y viviria en el respaldo. Alternativas:

- *Excepcion para Z.AI solo en el revisor.* **Descartada**: el revisor recibe la respuesta del alumno, que es justo el dato que mas importa proteger; una excepcion ahi vacia el control.
- *Un modelo de otra familia* (para el revisor no hay mas restriccion que no ser DeepSeek). **Descartada**: exigiria medir su calidad desde cero.
- *`z-ai/glm-5.3-flash`*. **Elegida.** Es el modelo que ya era el respaldo del revisor en Hugging Face, y su calidad en ese rol esta medida: la comparativa primario/respaldo de §5.7 del capstone corrio dos ejecuciones completas con los cuatro roles en el respaldo, revisor GLM-5.3-Flash incluido, con calidad equivalente en lo esencial. Mantiene la diversidad de familia con el evaluador (DeepSeek frente a GLM), que es la restriccion propia del revisor. Tiene 21 proveedores dentro de la politica. Y cuesta menos por token (0,15/0,50 USD por millon frente a 0,37/1,25).

Efectos colaterales: el respaldo del revisor deja de ser la excepcion de `litellm-huggingface-fallback` -- ahora es el mismo modelo en otro proveedor, como en los demas roles--, y revisor y validador comparten modelo. Lo segundo no rompe ninguna restriccion: hacen tareas distintas y la diversidad que se exige es entre evaluador y revisor.

El cambio de modelo se hace en el `.env` (`REVIEWER_MODEL`), como todos: la configuracion no fija modelos primarios. `.env.example` lo recomienda.

### Decision 5: la politica se escribe una vez, con un ancla YAML

La politica se declara en el primer deployment (`extra_body: &openrouter_provider_policy`) y los otros cuatro la referencian (`extra_body: *openrouter_provider_policy`). `yaml.safe_load`, que es lo que usan LiteLLM y la comprobacion estatica, resuelve el alias como el mismo objeto.

**Alternativas descartadas:** repetirla cinco veces (cinco listas de 25 slugs que pueden divergir en una edicion), o una clave de nivel superior tipo `x-openrouter-policy` (no esta verificado que LiteLLM ignore claves desconocidas en la raiz de su configuracion; el ancla dentro de un deployment no introduce nada que LiteLLM no conozca ya).

### Decision 6: el respaldo de Hugging Face se mantiene, fuera de la politica

Un 404 por politica es un fallo del primario, y LiteLLM aplica el fallback (Context). Ese camino no lleva ninguna politica de enrutado: Hugging Face elige su proveedor de inferencia. Desde el agente es silencioso: recibe una respuesta valida y no inspecciona la cabecera de fallback.

Se mantiene porque es el mismo comportamiento que antes de este change (no es una regresion), y porque retirarlo cambiaria la disponibilidad del sistema, que es otra decision. Lo que si hace este change es **dejarlo escrito** en la configuracion y en la spec, y no presentar la politica como cobertura total. Las mitigaciones posibles van como seguimiento: fijar el proveedor de inferencia de Hugging Face en el modelo (`huggingface/<proveedor>/<org>/<modelo>`) con el mismo criterio de jurisdiccion, o retirar el respaldo de los alias que reciben datos de clientes.

**Alternativa descartada:** `allow_fallbacks: false` u otra opcion de OpenRouter. No afecta a esto: el fallback que importa es el de LiteLLM a otro proveedor, no el interno de OpenRouter.

### Decision 7: la invariante se verifica en la comprobacion estatica existente

`verify_guardrail_coverage.py` suma una tercera invariante: todo deployment cuyo modelo no empieza por `huggingface/` (los de `os.environ/...` se tratan como de OpenRouter, que es la convencion de `.env.example`) lleva `extra_body.provider` con `data_collection: "deny"`, `zdr: true` y una lista `only` no vacia. Corre en el job `litellm-guardrails` ya existente, sin tocar el workflow.

**Alternativa descartada:** un script aparte y un paso nuevo de CI. Es la misma clase de comprobacion (una propiedad de privacidad del proxy que no se puede olvidar en un deployment nuevo), sobre el mismo fichero y con el mismo disparador.

## Risks / Trade-offs

- [Un cliente con virtual key puede sustituir la politica enviando la clave literal `extra_body` en el JSON] → Comprobado en 1.106.0. Ningun agente ni el juez lo hacen: `ChatOpenAI(extra_body=...)` aplana el contenido en el nivel superior del JSON, y el juez envia solo `model` y `messages`. El escenario de abuso exige controlar el codigo de un agente o robar su key, que ya permite cosas peores. Mitigacion recomendada como defensa adicional: activar ZDR y la lista de proveedores permitidos tambien a nivel de cuenta en OpenRouter, que una peticion no puede relajar.
- [El respaldo de Hugging Face no tiene politica] → Documentado (decision 6). La politica puede aumentar la fraccion de llamadas que caen al respaldo si los proveedores permitidos fallan; la verificacion (tareas 3.x) comprueba que cada alias responde desde el primario y no desde el respaldo.
- [`REVIEWER_MODEL` sin actualizar en un despliegue] → El revisor fallaria siempre con 404 y viviria en el respaldo, sin error visible para el agente. Mitigacion: el cambio se anuncia como BREAKING en la propuesta y en el PR, `.env.example` lo recomienda, y el 404 de OpenRouter nombra a `z-ai` como unico proveedor disponible, que es diagnostico suficiente en los logs.
- [Certificacion DPF no verificada proveedor a proveedor] → Riesgo residual explicito (decision 3). Seguimiento: comprobar cada proveedor estadounidense en la lista publica del DPF y retirar de `only` los no certificados.
- [Sede no es centro de datos] → Un proveedor con sede en el EEE puede procesar fuera, y uno estadounidense puede hacerlo en la UE. La lista controla con quien se contrata (el responsable juridico del tratamiento), que es lo que OpenRouter publica de forma sistematica.
- [La lista envejece] → Un proveedor nuevo y conforme no recibe trafico hasta que se anada (fail-closed, deliberado). Un proveedor de la lista que cambie de sede o de politica de datos sigue cubierto por `zdr` y `deny`, que OpenRouter evalua en cada llamada.
- [Latencia] → Restringir proveedores puede empeorar la latencia del camino sincrono (evaluador, revisor, validador). La verificacion con `evals.run --mode real` mide las latencias con la politica activa.

## Migration Plan

1. Desplegar la configuracion nueva.
2. En el `.env` de cada despliegue: `REVIEWER_MODEL=openrouter/z-ai/glm-5.3-flash`.
3. `docker compose up -d litellm` para recargar la configuracion y el entorno.
4. No hay que reaprovisionar virtual keys: los alias logicos y sus listas de modelos permitidos no cambian.

Rollback: revertir el commit y restaurar `REVIEWER_MODEL`. Ninguna migracion de datos.
