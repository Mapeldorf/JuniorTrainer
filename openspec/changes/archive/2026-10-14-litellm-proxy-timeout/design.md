# Design

## Context

Ver `proposal.md` para la motivacion. Estado tecnico relevante:

- `infra/litellm/config.yaml` tiene `model_list` (3 modelos logicos: `generator`, `evaluator`, `reviewer`, todos via OpenRouter segun `.env`), `litellm_settings` (callbacks de Langfuse) y, desde `litellm-virtual-keys`, `general_settings` (`master_key`, `database_url`).
- Cada agente ya fija `timeout=45.0` en su cliente `ChatOpenAI` (`agents/*/app/llm.py`), cubriendo el requirement "Timeout explicito en las llamadas al LLM" de `agent-resilience`.
- Los 3 modelos logicos van todos por el mismo proveedor (OpenRouter) con latencia esperada similar -- no hay un modelo con un perfil de latencia claramente distinto que justifique timeouts diferenciados.

## Goals / Non-Goals

**Goals:**
- Que una llamada de LiteLLM al proveedor subyacente que se cuelgue falle con un error propio del proxy, acotado en tiempo, sin depender de que el timeout del cliente (45s) sea quien corte la conexion.
- Verificar el comportamiento real sin depender de que un proveedor real tarde lo suficiente ni esperar minutos.

**Non-Goals:**
- No se añaden timeouts diferenciados por modelo: los 3 van por el mismo proveedor con latencia similar: `litellm_settings.request_timeout` (global) cubre los 3 sin necesidad de repetir `timeout` en cada entrada de `litellm_params`.
- No se cambia el timeout de 45s de los agentes ni los backstops de 120s/300s del backend: siguen siendo necesarios como ultima red de seguridad (p. ej. si el propio proceso de LiteLLM se cuelga por completo, no solo la llamada al proveedor).

## Decisions

- **`litellm_settings.request_timeout`, no `litellm_params.timeout` por modelo.** Alternativa descartada: repetir `timeout: 40` en las 3 entradas de `model_list`. Se descarta porque los 3 modelos comparten proveedor y perfil de latencia esperado; el ajuste global es mas simple de mantener y evita que alguien añada un cuarto modelo en el futuro y se olvide de ponerle timeout. Si algun dia un modelo tuviera un perfil de latencia claramente distinto (p. ej. un modelo de razonamiento mucho mas lento), seria el momento de revisar esta decision y añadir un override puntual en su `litellm_params`.
- **Valor: 40 segundos, por debajo del timeout de 45s del cliente.** Si el timeout del proxy fuera igual o mayor que el del cliente, el cliente cortaria la conexion primero con un error de socket generico (p. ej. `httpx.ReadTimeout`), y el timeout del proxy nunca llegaria a activarse en la practica -- quedaria como configuracion muerta. Poniendolo por debajo (40s vs 45s), LiteLLM es quien corta primero y devuelve un error estructurado (`litellm.Timeout`, con forma de error HTTP reconocible) en vez de que el cliente vea solo una conexion cortada. El margen de 5s no es critico en si mismo; lo importante es que exista margen suficiente para que la respuesta de error de LiteLLM tenga tiempo de viajar de vuelta al cliente antes de que el propio timeout del cliente expire.
- **`litellm_settings.num_retries: 0`, descubierto durante la verificacion, no planeado en el diseño original.** Con `request_timeout` solo, LiteLLM reintenta tras un timeout (comportamiento por defecto del SDK), y el tiempo total hasta el error final observado fue de 125s (varios intentos de 40s cada uno) -- muy por encima de los 45s del cliente, exactamente lo que `request_timeout=40` queria evitar (que el proxy falle dentro de la ventana del cliente). Con `num_retries: 0`, un unico intento corta a los ~40s de verdad (verificado: `time taken=40.12 seconds`). Sin reintentos a nivel de proxy no se pierde resiliencia: las llamadas de los agentes ya son de un solo intento (no hay logica de reintento en `agents/*/app/service.py`), asi que un reintento automatico en LiteLLM no estaba comprando nada -- solo alargaba el tiempo hasta el error sin que ningun agente lo aprovechara.
- **Verificacion con un servidor HTTP de prueba que responde deliberadamente tarde, no con el proveedor real.** Esperar a que OpenRouter tarde mas de 40s de forma natural no es practico ni reproducible. En su lugar: levantar un servidor HTTP minimo (un script de una linea con `http.server`, o equivalente) que acepta la peticion y duerme mas tiempo del timeout configurado antes de responder, añadirlo temporalmente como una entrada mas de `model_list` apuntando su `api_base` a ese servidor, y comprobar que LiteLLM corta la llamada en ~40s con un error de timeout en vez de esperar a que el servidor de prueba responda. Es una verificacion manual, no un test automatizado permanente -- el servidor de prueba y la entrada de `model_list` se retiran despues de verificar.

## Risks / Trade-offs

- [Si en el futuro se añade un modelo con latencia esperada mucho mayor (p. ej. razonamiento extendido), el timeout global de 40s lo cortaria antes de tiempo] → Mitigacion: documentado en Non-Goals; el ajuste en ese momento es añadir un `timeout` especifico en el `litellm_params` de esa entrada, que sobreescribe el global solo para ese modelo.
- [40s es una cifra razonada pero no derivada de datos reales de latencia de OpenRouter en produccion] → Mitigacion: es una red de seguridad adicional, no el mecanismo principal (el cliente ya corta a los 45s); si demuestra ser demasiado ajustado en uso real (timeouts del proxy en llamadas que habrian terminado bien), es un ajuste de una sola linea en `config.yaml`.
