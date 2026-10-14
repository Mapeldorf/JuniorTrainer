# Design

## Context

Los 5 agentes montan FastAPI puro (`agents/{code,evaluator,exercises,reviewer,web}/app/main.py`) via `add_a2a_routes_to_fastapi(app, agent_card_routes=..., jsonrpc_routes=...)`, sin ningun middleware de autenticacion. El backend llama a los 5 desde un unico punto, `backend/app/a2a_client.py::send_a2a_task`, usado tanto por `backend/app/orchestrator.py` (generacion de ejercicios) como por `backend/app/answer_orchestrator.py` (evaluacion de respuestas); ese cliente construye su propio `httpx.AsyncClient` y lo pasa a `create_client` del SDK A2A.

Las credenciales ya siguen un patron establecido en todo el proyecto: cada servicio (backend y los 5 agentes) carga su propio `Settings` (pydantic-settings) desde el mismo `.env` en la raiz del repo (ver `agents/code/app/config.py`, `backend/app/config.py`), duplicando las variables que necesita en vez de compartir codigo entre servicios. Las credenciales de GitHub App ya siguen exactamente este patron (copiadas en backend y en el agente de codigo).

Ver proposal.md - Why para la motivacion del cambio.

## Goals / Non-Goals

**Goals:**
- Una unica credencial de servicio compartida, verificada de forma identica en los 5 agentes.
- Cero cambio de comportamiento para una peticion ya autenticada (trace_id, formato de respuesta A2A, timeouts existentes).
- Rechazo antes de cualquier coste (LLM, GitHub, Tavily, DB): la verificacion debe ocurrir en middleware HTTP, antes del `DefaultRequestHandler`/`AgentExecutor`.

**Non-Goals:**
- No se implementa JWT firmado, rotacion automatica de credenciales, ni un servicio de identidad. Se trata de un secreto compartido simple, adecuado a una red interna de docker-compose con un unico backend como llamador legitimo.
- No se autentica ni autoriza por rol/usuario final dentro del agente (eso ya lo hace el backend con `require_tech_lead`/RLS antes de llegar aqui) -- esta capa solo responde a "¿esta peticion viene del backend?".
- No cubre la Agent Card publica (`create_agent_card_routes`): ver decision mas abajo.

## Decisions

### Mecanismo: cabecera `X-Agent-Service-Token` + API key compartida, no JWT

**Alternativas consideradas:**
- *JWT firmado (asimetrico)*: anade una clave privada/publica, rotacion y expiracion a gestionar en 6 servicios para un escenario de confianza de 1 llamador (el backend) a 5 destinos, dentro de una red interna. Complejidad sin beneficio proporcional aqui.
- *mTLS entre backend y agentes*: requiere gestion de certificados por servicio en docker-compose/despliegue; de nuevo, complejidad desproporcionada para cerrar "cualquiera que alcance el puerto".
- **Elegida: API key compartida en una cabecera HTTP, comparada en tiempo constante.** Mismo nivel de proteccion que necesita el caso de uso (un unico llamador de confianza, red interna), coherente con como ya se gestionan el resto de secretos del proyecto (variable en el `.env` compartido, cargada por `Settings` de cada servicio), y no anade dependencias nuevas.

### Punto de verificacion: middleware FastAPI (`@app.middleware("http")`), no `Depends`

Los 5 `main.py` llaman a `add_a2a_routes_to_fastapi`, que registra las rutas A2A internamente sin exponer un punto donde inyectar `Depends` por ruta sin tocar el SDK. Un middleware HTTP de FastAPI, montado antes de esa llamada, intercepta toda peticion a la app (incluida la Agent Card, ver mas abajo) sin depender de como el SDK define sus rutas internamente -- mas robusto frente a cambios futuros del SDK que anadiendo `Depends` ruta a ruta.

### Alcance: la Agent Card tambien exige credencial

`create_agent_card_routes` publica el "menu" del agente (capacidades, URL, version). No contiene secretos de negocio, pero sí confirma que un agente concreto existe y en qué URL, información de reconocimiento (ver Risks: "Non-Goals" no cubre un modelo de amenaza frente a *fingerprinting*). Como no hay ningun consumidor legitimo de la Agent Card fuera del backend hoy, se protege con la misma credencial: mantiene el mecanismo uniforme (requisito "Mismo formato de rechazo en cualquier agente") y evita tener que mantener una lista de rutas "publicas" frente a "privadas" en 5 sitios.

### Origen de la credencial: nueva variable en el `.env` compartido, mismo patron que el resto

`AGENT_SERVICE_TOKEN` (nombre propuesto) se anade a `.env.example` en la raiz, y cada `Settings` (backend y los 5 agentes) la carga como campo obligatorio (`str`, sin default), igual que `litellm_master_key` o `github_app_private_key` ya hacen. No se introduce un gestor de secretos nuevo porque el proyecto no usa uno hoy para ningun otro secreto -- coherencia con el resto del sistema, no una decision de seguridad ideal en abstracto.

### Comparacion en tiempo constante

La comparacion del valor recibido contra el configurado SHALL usar `hmac.compare_digest` (o equivalente), no `==`, para no introducir un canal de temporizacion que facilite adivinar la credencial por fuerza bruta remota -- barato de hacer bien desde el principio.

## Risks / Trade-offs

- **[Riesgo] Secreto compartido unico**: si se filtra, compromete los 5 agentes a la vez (no hay aislamiento por agente). → *Mitigacion*: es el mismo radio de exposicion que ya tienen hoy `litellm_master_key` o las credenciales de GitHub App en este proyecto; aceptable para esta topología (1 backend, red interna). Rotarlo es tan simple como cambiar una variable de entorno en 6 sitios.
- **[Riesgo] Mismatch de despliegue**: si un agente se despliega con la variable vieja mientras el backend ya rota a la nueva, ese agente rechaza todo el trafico legitimo. → *Mitigacion*: el Migration Plan abajo secuencia el despliegue para evitarlo.
- **[Trade-off] No hay identidad diferenciada entre agentes ni rotacion automatica.** Aceptado como Non-Goal: resolver la ausencia total de autenticacion es la prioridad; una solucion mas sofisticada puede ser una propuesta posterior si el proyecto crece a mas de un llamador legitimo.

## Migration Plan

1. Anadir `AGENT_SERVICE_TOKEN` a `.env.example` (valor de ejemplo) y generar el valor real en cada entorno (local/staging/produccion) sin commitearlo.
2. Desplegar primero los 5 agentes con el middleware **en modo permisivo** no es una opcion aqui (no existe ese modo en el diseño: la verificacion es binaria). En su lugar, desplegar backend y los 5 agentes en la misma ventana de despliegue (docker-compose los levanta juntos de todas formas en este proyecto), con la variable ya presente en el `.env` compartido antes de reconstruir cualquier contenedor.
3. Verificar manualmente tras el despliegue: una generacion y una evaluacion de prueba de extremo a extremo deben completarse con normalidad; una llamada directa a cualquier agente sin cabecera debe devolver `401`.
4. **Rollback**: revertir el commit retira el middleware y el envio de la cabecera a la vez (mismo cambio), sin estado persistente que limpiar -- rollback simple de codigo.
