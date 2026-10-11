# Tasks

## 1. Esquema de memoria y roles de Postgres

- [x] 1.1 Escribir `infra/supabase/migrations/0003_agents_memory.sql`: esquema `memory`, rol `agents_memory` (`USAGE`+`CREATE` solo sobre `memory`), rol `agents_exercise_reader` (`SELECT` solo sobre `public.exercise`), contraseñas via variables de entorno al aplicar (no hardcodeadas)
- [x] 1.2 Aplicar la migracion al proyecto `uwgqxdfpkkbenmynwlmk` y verificar con `execute_sql` que el esquema `memory` y los dos roles existen, y que `agents_memory` no tiene privilegios sobre `public`
- [x] 1.3 Añadir a `.env.example` las variables de conexion directa a Postgres (host/puerto/nombre de BD de Supabase, contraseñas de `agents_memory` y `agents_exercise_reader`), con comentarios de donde sacarlas

## 2. Servicio A2A de prueba (desechable)

- [x] 2.1 Montar un servicio A2A minimo local con `a2a-sdk` (Agent Card + una skill de eco) y verificar que un cliente A2A de prueba le manda una tarea y recibe el resultado esperado
- [x] 2.2 Confirmar el patron de cableado (Agent Card, cliente A2A sincrono sin streaming) a reutilizar en los tres agentes reales; este servicio de prueba no se añade al repo final ni a `docker-compose.yml`

## 3. Agente Web

- [ ] 3.1 Scaffold `agents/web/` (servicio A2A con Agent Card en `/.well-known/agent-card.json`) y verificar que arranca y responde a su Agent Card
- [ ] 3.2 Implementar la tool `tavily_search` (hasta 5 busquedas por tarea) y verificar con una llamada real que devuelve titulo, URL y extracto
- [ ] 3.3 Conectar al modelo `generator` via el proxy de LiteLLM (`langchain-openai` contra `http://litellm:4000`, autenticado con `LITELLM_MASTER_KEY`) y verificar que una llamada de prueba responde con un resumen por tecnologia
- [ ] 3.4 Implementar memoria larga (`PostgresStore`, clave = tecnologias normalizadas, TTL 30 dias) y verificar que una segunda llamada con las mismas tecnologias no invoca `tavily_search` (requisito "El agente web no repite busquedas")
- [ ] 3.5 Implementar memoria corta (`PostgresSaver`, `thread_id` = id de generacion + nombre del agente) y verificar que sus checkpoints se borran al terminar la tarea (Ready o error)
- [ ] 3.6 Leer el `trace_id` de Langfuse de los metadatos del mensaje A2A recibido y usarlo en las llamadas al modelo; verificar en Langfuse que la traza de esta tarea aparece bajo ese id, con `memory_hit=true` cuando aplica

## 4. Agente Codigo

- [ ] 4.1 Scaffold `agents/code/` y verificar su Agent Card
- [ ] 4.2 Implementar `list_files`/`read_file` de solo lectura, limitadas a la carpeta del repo preparada, hasta 10 ficheros leidos por tarea, y verificar que una ruta fuera de esa carpeta se rechaza
- [ ] 4.3 Conectar al modelo `generator` via LiteLLM y verificar con un repo de prueba que devuelve resumen, tecnologias detectadas y hasta 10 fragmentos (fichero, linea inicial, codigo, nota) de 12 lineas maximo
- [ ] 4.4 Implementar memoria larga (clave = SHA-256 del repo o URL+commit, mas tecnologias; TTL 30 dias) y verificar que una segunda llamada con el mismo repo y tecnologias no relee ningun fichero (requisito "El agente de codigo no relee el mismo repositorio")
- [ ] 4.5 Propagar el `trace_id` de Langfuse recibido y verificar la traza de esta tarea, con `memory_hit=true` cuando aplica

## 5. Agente Ejercicios

- [ ] 5.1 Scaffold `agents/exercises/` y verificar su Agent Card
- [ ] 5.2 Implementar `search_saved_exercises` (conexion de solo lectura con el rol `agents_exercise_reader`, hasta 3 consultas por tarea, hasta 10 resultados, solo `saved = true` y `deleted_at` nulo) y verificar que un ejercicio no guardado o eliminado nunca aparece en el resultado
- [ ] 5.3 Implementar la decision y redaccion de 1 a 5 ejercicios candidatos (enunciado, codigo con el cambio en debug, respuesta esperada) a partir de los resultados de web/codigo, el tipo y el numero pedidos, y verificar con una llamada de prueba que la salida trae exactamente el numero pedido con esos cuatro campos
- [ ] 5.4 Implementar memoria larga (clave = tipo; sin caducidad), incluyendo en el prompt los 20 enunciados mas recientes de ese tipo, y verificar que una segunda generacion del mismo tipo no repite el tema de un enunciado ya propuesto (requisito "El agente de ejercicios no repite temas ya propuestos")
- [ ] 5.5 Propagar el `trace_id` de Langfuse recibido y verificar la traza de esta tarea

## 6. Orquestacion en FastAPI

- [ ] 6.1 Cliente A2A en FastAPI para enviar tareas sincronas (sin streaming) a los tres agentes, y verificar con una llamada de prueba a cada uno que la respuesta llega como artefacto JSON
- [ ] 6.2 Endpoint para iniciar una generacion (tecnologias, repo opcional, tipo, numero entre 1 y 5) que valida la entrada (requisitos "Entrada minima" y "Numero de ejercicios candidatos") y lanza la orquestacion en una tarea de fondo; verificar que la respuesta HTTP llega con un id de generacion antes de que los agentes terminen
- [ ] 6.3 Endpoint para consultar el estado de una generacion (en curso / Ready con candidatos / error con mensaje) y verificar los tres estados con generaciones de prueba
- [ ] 6.4 Orquestacion en paralelo de web+codigo (codigo solo si hay repositorio), espera a que ambos terminen, y entonces llamada a ejercicios con sus resultados, el tipo y el numero; verificar el caso con repositorio y el caso sin repositorio (requisito "Orquestacion en paralelo de los agentes de entrada")
- [ ] 6.5 Manejo de fallos parciales: si falla el agente web habiendo repositorio, la generacion sigue sin fuentes de internet; si falla el de codigo, el de ejercicios, o el web sin repositorio, la generacion queda en error con el mensaje; verificar cada uno de los tres casos forzando el fallo del agente correspondiente
- [ ] 6.6 Limites de tiempo (`asyncio.wait_for`: 2 minutos por tarea A2A, 5 minutos por generacion completa) y verificar con una tarea simulada lenta que la generacion termina en error por tiempo excedido
- [ ] 6.7 Generar un `trace_id` de Langfuse por generacion y propagarlo en los metadatos del mensaje A2A a los tres agentes; verificar en Langfuse que las llamadas de una misma generacion aparecen agrupadas bajo esa traza

## 7. docker-compose

- [ ] 7.1 Añadir los servicios `agent-web`, `agent-code` y `agent-exercises` a `docker-compose.yml` (sin publicar puerto al host, solo red interna de Compose), con sus variables de entorno via `.env`, y verificar `docker compose config` sin errores
- [ ] 7.2 Verificar `docker compose build` sin errores para los tres servicios nuevos (requiere Docker en la maquina del usuario)

## 8. Prueba de aceptacion de extremo a extremo

- [ ] 8.1 Lanzar una generacion con el repo real de Pokemon (clonado o subido) y tecnologias reales, y verificar que termina en Ready con entre 1 y 5 candidatos
- [ ] 8.2 Verificar en Langfuse que las trazas de los tres agentes de esa generacion aparecen agrupadas bajo el mismo `trace_id`
- [ ] 8.3 Repetir la generacion con el mismo repo y las mismas tecnologias, y verificar que el agente web no llama a `tavily_search`, el agente de codigo no relee ficheros (ambos con `memory_hit=true` en su traza), y el agente de ejercicios no repite el tema de un enunciado ya propuesto

## Workflow follow-up

- Archivar el cambio (`/opsx:archive`) cuando los grupos 7 y 8 esten completos, incluida la prueba de aceptacion con el repo de Pokemon contra la infraestructura real del usuario (LiteLLM/OpenRouter, Tavily, Langfuse, Docker).
