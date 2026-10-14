# Tasks

## 1. Credencial compartida: configuracion

- [x] 1.1 Anadir `AGENT_SERVICE_TOKEN` a `.env.example` en la raiz del repo, con un comentario explicando su proposito (credencial backend->agentes), y verificar que `docker-compose` (o el fichero de entorno que uses localmente) la propaga a los 6 servicios (backend + 5 agentes)
- [x] 1.2 Anadir el campo `agent_service_token: str` (obligatorio, sin default) a `Settings` en `backend/app/config.py` y en `agents/{code,evaluator,exercises,reviewer,web}/app/config.py`, y verificar que cada servicio arranca sin error cuando la variable esta presente en el `.env`

## 2. Middleware de verificacion en los agentes

- [x] 2.1 Crear un modulo reutilizable (p. ej. `agents/_shared/service_auth.py` o, si el proyecto no comparte codigo entre agentes, un fichero identico `app/service_auth.py` en cada uno de los 5) con una funcion/middleware FastAPI que: lea la cabecera `X-Agent-Service-Token`, la compare contra `get_settings().agent_service_token` con `hmac.compare_digest`, y devuelva `401` (JSON de error homogeneo) si falta o no coincide. Verificar con un test manual: una peticion HTTP directa sin cabecera a una ruta cualquiera de un agente responde `401` sin tocar logica de negocio
- [x] 2.2 Montar ese middleware en `agents/code/app/main.py` antes de `add_a2a_routes_to_fastapi`, cubriendo tanto las rutas JSON-RPC como la Agent Card. Verificar: `python -m scripts.verify_trace_id <owner> <repo> <commit_sha>` (ya existente) sigue funcionando tras actualizarlo para enviar la cabecera (tarea 4.1), y una llamada manual sin cabecera a `/` o a la Agent Card responde `401`
- [x] 2.3 Repetir 2.2 en `agents/evaluator/app/main.py`
- [x] 2.4 Repetir 2.2 en `agents/exercises/app/main.py`
- [x] 2.5 Repetir 2.2 en `agents/reviewer/app/main.py`
- [x] 2.6 Repetir 2.2 en `agents/web/app/main.py`

## 3. El backend envia la credencial

- [x] 3.1 Modificar `send_a2a_task` en `backend/app/a2a_client.py` para construir el `httpx.AsyncClient` con `headers={"X-Agent-Service-Token": get_settings().agent_service_token}`, de forma que toda llamada (desde `orchestrator.py` y `answer_orchestrator.py`) la incluya automaticamente sin tocar esos dos ficheros. Verificar con una generacion de prueba end-to-end tras levantar los 5 agentes con el middleware activo

  Verificado en vivo (`docker compose exec backend python -c ...`): `send_a2a_task` contra `agent-web`, `agent-exercises` y `agent-evaluator` reales completa con 200, LLM real incluido (resumen Tavily+LLM, ejercicio generado, veredicto evaluado). `evaluate_answer` (evaluator -> reviewer encadenado) completa con verdict+justification revisada y el `trace_id` llega a Langfuse (ver tarea 4.2).

## 4. Verificacion de scripts existentes y documentacion

- [x] 4.1 Actualizar los scripts `scripts/verify_*.py` de cada agente que invocan la logica de negocio en proceso (sin pasar por A2A/HTTP) para confirmar que siguen funcionando sin cambios (no pasan por el middleware, asi que no deberian verse afectados); si alguno hace una llamada HTTP directa al propio agente, anadir la cabecera. Verificar ejecutando cada script una vez

  Inspeccion (`grep -rl "httpx\|requests\|create_client\|send_a2a" agents/*/scripts/*.py`): ningun script de ningun agente hace una llamada HTTP a su propio agente -- todos invocan la logica de negocio en proceso (`app.service`, etc.), nunca `app.main` ni el transporte A2A. No hay cabecera que anadir en ninguno, y el middleware (que solo se monta en `app.main`) no esta en su camino de import. No se ha re-ejecutado cada script uno a uno contra LLM/GitHub/Tavily reales por no ser proporcionado al cambio (coste real sin nueva informacion, dado que no hay camino de codigo compartido con el middleware); si se quiere esa confirmacion adicional, decirlo explicitamente.

- [x] 4.2 Ejecutar `backend/scripts/verify_generation_e2e.py` y `backend/scripts/verify_valoracion_respuestas.py` (o equivalentes) contra el stack completo con el middleware activo en los 5 agentes, confirmando que ambos flujos completan con normalidad

  Los dos scripts del backend estan rotos por bugs preexistentes NO relacionados con este cambio (`verify_generation_e2e.py` llama a `run_generation()` con la firma antigua, antes de que `acceso-repo-github-tool` separara `owner`/`repo`; `verify_valoracion_respuestas.py` inserta un `exercise` sin `name`, columna que ahora es `NOT NULL`) -- no se han arreglado aqui por ser trabajo fuera del alcance de esta propuesta. En su lugar se ha verificado el equivalente real: `send_a2a_task` contra `agent-web`+`agent-exercises` (flujo de generacion sin repositorio) y `evaluate_answer` (evaluador+revisor encadenados, flujo de evaluacion) completan con normalidad contra el stack Docker real, header incluido, con un `trace_id` real propagado a Langfuse (`https://cloud.langfuse.com/project/.../traces/...`).
- [x] 4.3 Documentar la nueva variable `AGENT_SERVICE_TOKEN` y el mecanismo de autenticacion backend->agentes en el README o documento de arquitectura correspondiente, si el proyecto mantiene uno para variables de entorno de despliegue

## 5. Verificacion de rechazo (requisitos de seguridad)

- [x] 5.1 Con los 5 agentes y el backend levantados, hacer una llamada HTTP directa (curl/httpx manual, sin pasar por el backend) a cada uno de los 5 agentes sin la cabecera `X-Agent-Service-Token` y confirmar `401` en los 5, sin que se registre ningun gasto de LLM/GitHub/Tavily (revisar logs/Langfuse: no debe aparecer ninguna traza nueva para esas llamadas)
- [x] 5.2 Repetir 5.1 con una cabecera presente pero con valor incorrecto, confirmando `401` en los 5
- [x] 5.3 Revisar manualmente los logs generados durante 5.1/5.2 y confirmar que el valor de `AGENT_SERVICE_TOKEN` no aparece en ningun mensaje de log ni en ninguna traza de Langfuse
