# Proposal

## Why

`infra/litellm/config.yaml` no fija ninguna politica de enrutado de proveedores, asi que **OpenRouter elige en cada llamada el proveedor de inferencia** que sirve el modelo. Por esa ruta viajan el codigo propietario de los repositorios de los clientes (agentes de codigo y de ejercicios) y las respuestas de los alumnos ya redactadas por Presidio (evaluador y revisor). Entre los proveedores que hoy sirven DeepSeek V4.1 Flash hay empresas con sede en paises sin decision de adecuacion de la UE (China, Singapur), y nada impide que una llamada acabe en ellas. Es el riesgo 11 del capstone, de nivel Alto, con la decision de mitigarlo "como change propio": este.

Se comprobo contra la API de OpenRouter que **la retencion cero (ZDR) no basta**: el unico endpoint de `z-ai/glm-5.3-flashx` (Z.AI, Singapur) y el de SiliconFlow (Singapur) para DeepSeek figuran como ZDR y aceptan una llamada con `zdr: true` y `data_collection: "deny"`. La jurisdiccion necesita su propio control.

## What Changes

- Todo deployment servido por OpenRouter (`generator`, `evaluator`, `reviewer`, `validator` y `judge`) pasa a OpenRouter un objeto `provider` con tres restricciones: `data_collection: "deny"`, `zdr: true` y una **lista cerrada** (`only`) de proveedores con sede en el EEE o en un pais con decision de adecuacion de la UE. La politica se define una sola vez y se reutiliza en los cinco deployments.
- **BREAKING (modelo del revisor):** `z-ai/glm-5.3-flashx` solo lo sirve Z.AI, que la lista excluye. El primario del revisor pasa a `z-ai/glm-5.3-flash`, el mismo modelo que ya era su respaldo en Hugging Face y cuya calidad esta medida en la comparativa primario/respaldo de §5.7. Hay que cambiar `REVIEWER_MODEL` en el `.env` de cada despliegue; sin ese cambio, toda llamada del revisor acabaria en el respaldo.
- Una politica que no puede cumplirse **falla de forma explicita en OpenRouter** (HTTP 404, sin desviarse a otro proveedor de OpenRouter). Lo que hace LiteLLM despues, desviar al respaldo de Hugging Face, queda documentado tal cual: ese camino no esta cubierto por esta politica.
- La comprobacion estatica `infra/litellm/verify_guardrail_coverage.py` incorpora una tercera invariante: todo deployment que no sea de Hugging Face lleva la politica completa. Corre en el mismo job `litellm-guardrails` de CI, sin cambios en el workflow.
- `.env.example` recomienda `openrouter/z-ai/glm-5.3-flash` para `REVIEWER_MODEL` y avisa de que los cinco primarios tienen que ser modelos de OpenRouter. `evals/prices.json` asigna al revisor de produccion el modelo nuevo, para que el modelo de costes siga describiendo lo desplegado.

## Capabilities

### New Capabilities

- `llm-provider-routing`: que proveedores de inferencia pueden recibir el trafico de los modelos logicos servidos por un agregador, con que garantias de retencion y de jurisdiccion, como falla una politica imposible de cumplir y como se verifica de forma estatica.

### Modified Capabilities

Ninguna. El fallback a Hugging Face (`agent-resilience`) no cambia de comportamiento: una llamada rechazada por la politica es una llamada fallida mas, y se documenta en la capacidad nueva que el respaldo queda fuera de la politica.

## Impact

**Codigo y configuracion**

- `infra/litellm/config.yaml`: objeto `provider` en `extra_body` de los cinco deployments de OpenRouter; comentarios de cabecera y del respaldo del revisor.
- `infra/litellm/verify_guardrail_coverage.py`: tercera invariante y sus casos sinteticos.
- `.env.example`: recomendacion de `REVIEWER_MODEL` y aviso sobre el proveedor de los primarios.
- `evals/prices.json`: rol `production.reviewer`.

**Operacion**

- Cambiar `REVIEWER_MODEL=openrouter/z-ai/glm-5.3-flash` en el `.env` y reiniciar `litellm`. No hay que reaprovisionar virtual keys: los alias logicos no cambian.
- El coste por token del revisor baja (0,15/0,50 USD por millon frente a 0,37/1,25 de FlashX, precios de OpenRouter).

**Documentacion fuera de este change**

- `capstone/juniortrainer-capstone.md` (§3.3 tabla de modelos, §3.7 costes, §5.7, §6.7 y riesgo 11) describe aun FlashX como primario del revisor y el riesgo como abierto. No se toca aqui; se actualiza aparte.

**Fuera de alcance**

- Una politica equivalente para el respaldo de Hugging Face (fijar su proveedor de inferencia o retirar el respaldo de los alias con datos de clientes).
- La verificacion, proveedor a proveedor, de la certificacion en el Data Privacy Framework de los proveedores con sede en EE. UU.
- Los ajustes de privacidad de la cuenta de OpenRouter (ZDR y proveedores permitidos a nivel de cuenta).
