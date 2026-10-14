# Proposal

## Why

Ninguno de los 5 agentes LLM (`agents/code`, `agents/evaluator`, `agents/exercises`, `agents/reviewer`, `agents/web`) autentica las peticiones A2A que recibe: cualquiera que alcance su puerto puede invocarlos directamente, sin pasar por el backend orquestador. Esto invalida controles que el backend da por hechos (p. ej. `require_tech_lead`, la pertenencia de una respuesta a una asignacion) y expone sin limite los costes de LLM, GitHub API y Tavily a cualquier llamador. Hace falta cerrar esta puerta antes de que tenga sentido reforzar cualquier otra validacion aguas abajo.

## What Changes

- Cada uno de los 5 agentes SHALL exigir una credencial de servicio (API key compartida backend->agente) en toda peticion A2A, verificada por un middleware comun antes de que la peticion llegue a cualquier handler de negocio.
- El backend orquestador SHALL enviar esa credencial en cada llamada A2A a los 5 agentes (tanto para `exercise-generation` como para `answer-evaluation`).
- Una peticion sin credencial, con credencial invalida, o dirigida a `create_agent_card_routes` sin credencial SHALL recibir `401` sin ejecutar ninguna logica de negocio ni consumir presupuesto de LLM/GitHub/Tavily.
- La credencial SHALL cargarse desde configuracion/secretos (nunca hardcodeada), siguiendo el mismo patron ya usado para otras claves de agente (`app/config.py`).
- El mecanismo SHALL ser identico en los 5 agentes (mismo middleware, misma cabecera, mismo formato de error) para no crear 5 variantes de la misma proteccion.
- El `trace_id` existente (propagado a Langfuse) SHALL seguir funcionando sin cambios; esta autenticacion es una capa de transporte independiente, no sustituye ni se mezcla con la trazabilidad.
- **BREAKING**: tras este cambio, ninguna llamada directa a un agente sin la credencial de servicio funcionara, incluidas las de depuracion manual que se hagan hoy sin cabecera de autenticacion.

Fuera de alcance de esta propuesta (quedan para cambios posteriores ya identificados):
- Reactivar la validacion de `owner`/`repo` (hoy codigo muerto en `agents/code/app/github_ref.py`).
- Generalizar el aislamiento "dato no instruccion" en los prompts de `evaluator`, `reviewer` y `web`.
- Timeouts y rate limiting por cliente en los clientes LLM/Tavily.
- Redaccion de datos sensibles antes de enviarlos a Langfuse.

## Capabilities

### New Capabilities
- `agent-auth`: autenticacion de servicio (backend -> agente) para toda peticion A2A entrante a cualquiera de los 5 agentes LLM del sistema, incluyendo el comportamiento ante credencial ausente o invalida y el origen de la credencial.

### Modified Capabilities
(ninguna: `exercise-generation` y `answer-evaluation` orquestan los agentes pero no definen como se autentica el transporte A2A entre backend y agente, asi que no se modifican sus requisitos)

## Impact

- **Codigo afectado**: `agents/{code,evaluator,exercises,reviewer,web}/app/main.py` (montaje de middleware), `agents/{code,evaluator,exercises,reviewer,web}/app/config.py` (carga de la credencial), y `backend/app/a2a_client.py` (`send_a2a_task`, punto unico ya usado por `backend/app/orchestrator.py` y `backend/app/answer_orchestrator.py` para llamar a los 5 agentes -- anadir la cabecera de credencial aqui basta para cubrir ambos orquestadores).
- **Infra/config**: nueva variable de entorno/secreto para la credencial compartida, a definir en el entorno de despliegue de los 5 agentes y del backend.
- **Dependencias**: ninguna nueva libreria necesaria (autenticacion por cabecera HTTP simple sobre el transporte A2A ya existente).
- **Compatibilidad**: rompe cualquier llamada directa a un agente que no incluya la credencial (ver BREAKING arriba).
