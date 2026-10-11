# Proposal

## Why

JuniorTrainer no tiene todavia forma de producir ejercicios: el tech lead no puede generar nada a partir de un repositorio o unas tecnologias. Sin esto, los pasos siguientes del plan de trabajo (bloques, asignaciones, valoracion) no tienen con que trabajar. El paso 2 del plan de trabajo pide dejar la generacion funcionando de extremo a extremo, sin interfaz todavia, antes de construir nada mas encima.

## What Changes

- Un servicio A2A de prueba minimo, para validar el cableado FastAPI (orquestador/cliente A2A) <-> agente antes de construir los tres reales. No es una capability con comportamiento durable; se implementa y se descarta, documentado como paso de `design.md`/`tasks.md`.
- Tres agentes de generacion, cada uno un servicio A2A independiente con su Agent Card:
  - **Web**: busca documentacion de las tecnologias indicadas con `tavily_search`.
  - **Codigo**: lee el repo preparado con `list_files`/`read_file`, solo lectura.
  - **Ejercicios**: con los resultados de los dos anteriores, decide y redacta de 1 a 5 ejercicios candidatos, usando `search_saved_exercises` para no repetir enunciados ya guardados.
- Orquestacion en FastAPI: lanza web y codigo en paralelo (codigo solo si hay repositorio), espera a los dos, llama a ejercicios con sus resultados. Corre en tarea de fondo de la generacion, con limites de tiempo por tarea A2A y por generacion completa, y manejo de fallos parciales (sigue sin fuentes de internet si falla el web habiendo repo; error si falla el de codigo, el de ejercicios, o el web como unica entrada).
- Memoria de los tres agentes de generacion (LangChain/LangGraph, `PostgresSaver` de corto plazo por tarea y `PostgresStore` de largo plazo por agente), en un esquema `memory` nuevo de PostgreSQL con un usuario de base de datos limitado a ese esquema.
- Trazas de Langfuse por generacion, con el `trace_id` propagado a los tres agentes via metadatos del mensaje A2A, incluyendo `memory_hit` cuando una respuesta viene de memoria.
- Tres servicios nuevos en `docker-compose.yml` (uno por agente), hablando con LiteLLM via el modelo logico `generator`.
- Prueba de aceptacion: generar con el repo real de Pokemon, verificar las trazas en Langfuse, y verificar que una segunda generacion con el mismo repo y tecnologias no vuelve a llamar a Tavily ni a releer ficheros, y que el agente de ejercicios no repite enunciados ya propuestos.

**Fuera de alcance de este change** (van en el paso 3 del plan de trabajo): agentes evaluador y revisor, bloques (`block`, `block_exercise`), asignaciones (`assignment`, `assignment_exercise`), respuestas de alumnos (`answer`), y cualquier pantalla de frontend para generacion (el plan de trabajo dice explicitamente "sin interfaz todavia").

## Capabilities

### New Capabilities

- `exercise-generation`: el flujo de extremo a extremo que, a partir de unas tecnologias y opcionalmente un repositorio, orquesta los agentes web/codigo/ejercicios por A2A y produce de 1 a 5 ejercicios candidatos o un error, con sus limites y su manejo de fallos parciales.
- `agent-memory`: el comportamiento observable de la memoria de los agentes de generacion entre tareas (no repetir busquedas, lecturas de fichero ni temas de ejercicio ya vistos para la misma entrada), independientemente de que la implemente LangGraph.

### Modified Capabilities

(ninguna; `user-auth` y `data-authorization` no cambian sus requisitos en este change)

## Impact

- **Backend (FastAPI)**: nuevo orquestador/cliente A2A, endpoint(s) para lanzar una generacion y consultar su estado, tarea en segundo plano, lectura/escritura de `generation` y `exercise` (esquema ya existente en Supabase).
- **Tres servicios nuevos**: agentes `web`, `codigo` y `ejercicios`, cada uno un proceso Python con `a2a-sdk` + LangChain/LangGraph, añadidos a `docker-compose.yml`.
- **Base de datos**: esquema `memory` nuevo en el mismo Postgres de Supabase, con un rol `agents_memory` limitado a ese esquema (mas el rol de solo lectura del agente de ejercicios sobre `exercise`); migraciones nuevas en `infra/supabase/migrations/`.
- **LiteLLM**: sin cambios de configuracion (el modelo logico `generator` ya existe en `infra/litellm/config.yaml`); el usuario ya ha configurado `GENERATOR_MODEL`/`GENERATOR_API_KEY` (OpenRouter, `deepseek/deepseek-v4.1-flash`) y las claves de Tavily y Langfuse en `.env`.
- **Dependencias nuevas**: `a2a-sdk`, LangChain, `langgraph`, `langgraph-checkpoint-postgres`, cliente de Tavily, SDK de Langfuse.
- **Sin cambios en frontend**: este change no toca pantallas.
