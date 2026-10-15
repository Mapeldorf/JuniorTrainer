# Design

## Context

Ver `proposal.md` para la motivacion. Investigacion hecha contra la documentacion oficial de LiteLLM y Lakera (no supuesta):

- LiteLLM soporta guardrails declarados en `config.yaml` bajo una seccion `guardrails:` (distinta de `general_settings`/`litellm_settings`), cada uno con `guardrail_name`, `litellm_params.guardrail` (el tipo, p. ej. `lakera_v2`), `mode` (`pre_call`/`during_call`/`post_call`), y credenciales.
- `litellm_params.default_on: true` hace que el guardrail se ejecute en toda llamada, sin que el cliente tenga que listarlo en un campo `guardrails` de la peticion. Sin esto, haria falta tocar los 5 `agents/*/app/llm.py` para añadir ese campo a cada llamada -- con `default_on` no hace falta ningun cambio de codigo en los agentes.
- La integracion Lakera v2 de LiteLLM solo soporta `/v1/chat/completions`. Los 5 agentes llaman a LiteLLM via `langchain-openai` (`ChatOpenAI`), que usa ese mismo endpoint -- sin incompatibilidad.
- Un rechazo documentado tiene forma `{"error": {"message": "...", "type": "...", "param": null, "code": "400"}}`. Mismo patron que el `422 budget_exceeded` ya verificado en la propuesta anterior: sube sin capturar por `langchain-openai` hasta el framework A2A, que lo convierte en tarea fallida.
- El usuario ya tiene cuenta, proyecto y politica creados en la plataforma de Lakera (fuera de este repo); solo hace falta la API key en `.env`.

## Goals / Non-Goals

**Goals:**
- Deteccion automatizada de prompt injection, activa por defecto en los 5 agentes, sin tocar su codigo.
- Que un intento bloqueado no gaste presupuesto de LiteLLM (budget de `litellm-virtual-keys`) en la llamada al proveedor.

**Non-Goals:**
- No se gestiona el coste de Lakera desde este repo: es una facturacion separada de la de los modelos LLM, en la propia plataforma de Lakera. Si en el futuro se quisiera un techo de gasto en Lakera, es una propuesta aparte (y dependeria de lo que la plataforma de Lakera ofrezca para eso, no de LiteLLM).
- No se configura que deteccion exactamente corre (prompt injection vs jailbreak vs PII, sensibilidad): eso lo determina la politica que el usuario ya configuro en el proyecto de Lakera, no `config.yaml`. Si se quisiera ajustar, es un cambio en la plataforma de Lakera, no en este repo.
- No se quita la mitigacion existente (delimitadores + instruccion defensiva): son capas independientes (una es instruccion al modelo, la otra es deteccion antes de llegar a el); quitar la primera no aportaria nada y perderia defensa en profundidad si Lakera tuviera un falso negativo.

## Decisions

- **`mode: pre_call`, no `during_call`.** Decision del usuario: bloquear antes de llamar al proveedor, para no gastar presupuesto en una llamada ya identificada como maliciosa. Coste: mas latencia total en el camino feliz (Lakera corre antes del LLM, en serie, no en paralelo) -- aceptado como trade-off explicito.
- **`on_flagged`/accion: bloquear, no solo monitorizar.** Decision del usuario: un guardrail que no bloquea nada no protege nada; el riesgo de falsos positivos se acepta como parte de tener proteccion real, no como motivo para no usarla.
- **`default_on: true`, aplicado a los 5 agentes por igual, sin excepciones.** Alternativa descartada: aplicarlo solo a los agentes que manejan contenido no confiable mas directamente (evaluator, reviewer, web, code), dejando fuera a exercises. Se descarta porque la granularidad de LiteLLM para esto es binaria a nivel de proxy (`default_on` es todo-o-nada; la alternativa seria que cada agente mandara explicitamente `"guardrails": ["lakera-guard"]` en su llamada, lo que si requeriria tocar los 5 `llm.py` para una ganancia marginal: aplicarlo de mas a un agente que no lo necesita no tiene coste de seguridad, solo de latencia/Lakera-calls, y mantener la cobertura uniforme es mas simple de razonar y auditar que una lista de excepciones).
- **Variable de entorno `LAKERA_API_KEY`, nombre tal cual lo usa la documentacion de LiteLLM/Lakera.** Se mantiene el nombre de la convencion externa en vez de adaptarlo al patron `AGENT_*` del proyecto, porque esta key no es por-agente (es una sola, compartida por los 5, igual que `TAVILY_API_KEY`).

## Risks / Trade-offs

- [Falsos positivos: Lakera podria marcar como injection contenido legitimo, especialmente en `agent-code` (contenido de ficheros de repos reales, que puede incluir comentarios o strings con frases que coincidan con patrones de injection)] → Mitigacion: es el motivo por el que la pregunta de bloquear-vs-monitorizar se hizo explicita al usuario; si en uso real los falsos positivos resultan frecuentes, el ajuste es ir a `mode: monitor`-equivalente o afinar la politica en la plataforma de Lakera, sin tocar codigo.
- [Latencia adicional en todo el camino feliz, en los 5 agentes, no solo en los que manejan contenido no confiable] → Mitigacion: aceptado explicitamente (ver Decisions); el timeout de 45s de cada agente y el de 120s del backend (`agent-resilience`) ya tienen margen para absorber la latencia extra de un `pre_call`.
- [Dependencia de disponibilidad de un tercero: si Lakera no responde, `pre_call` bloquea toda llamada de los 5 agentes hasta que el guardrail resuelva o falle] → Verificado en tasks.md (grupo 4): LiteLLM falla cerrado (bloquea, no deja pasar) ante auth invalida (`401`, instantaneo) y ante conexion rechazada (`500`, 1s, proceso sigue vivo) -- comportamiento correcto y seguro por defecto.
- [**Hallazgo real durante la verificacion, no previsto**: si la direccion de Lakera resulta directamente inalcanzable a nivel de red (IP no enrutable, no solo puerto cerrado), el proceso de `litellm` crashea con SIGSEGV -- tumba el proxy entero para los 5 agentes, no solo bloquea la llamada que lo disparo] → Mitigacion aplicada: `restart: unless-stopped` en el servicio `litellm` de `docker-compose.yml` (no tenia ninguna politica de reinicio hasta ahora). No se investigo la causa raiz exacta del crash (posible bug en como LiteLLM/su stack async maneja ciertas direcciones no enrutables) -- se opto por la mitigacion operativa simple en vez de depurar una libreria externa; si se repitiera con frecuencia en uso real, ameritaria abrir un issue en el repo de LiteLLM.
