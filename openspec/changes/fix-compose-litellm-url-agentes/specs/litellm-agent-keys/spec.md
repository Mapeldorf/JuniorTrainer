# Spec Delta

## ADDED Requirements

### Requirement: Los agentes en contenedor llegan al proxy por su URL interna
El sistema SHALL hacer que cada uno de los 6 agentes, cuando se ejecuta como contenedor del stack de Docker Compose, envie sus llamadas al proxy de LiteLLM por la URL interna de la red de Compose (`http://litellm:4000/v1`), con independencia del valor que tenga `LITELLM_BASE_URL` en el `.env` compartido de la raiz. Un valor de `LITELLM_BASE_URL` pensado para procesos del host (por ejemplo `http://localhost:4000/v1`, el que usa el arnes de evaluacion) SHALL NOT llegar a los agentes en contenedor.

#### Scenario: El .env apunta a localhost para el host
- **WHEN** el `.env` de la raiz contiene `LITELLM_BASE_URL=http://localhost:4000/v1` y se recrea el stack de Docker Compose
- **THEN** cada uno de los 6 agentes tiene `LITELLM_BASE_URL=http://litellm:4000/v1` en su entorno
- **AND** sus llamadas al modelo llegan a LiteLLM sin `APIConnectionError`

#### Scenario: El .env no define la variable
- **WHEN** el `.env` de la raiz no contiene `LITELLM_BASE_URL` y se recrea el stack
- **THEN** cada uno de los 6 agentes usa igualmente `http://litellm:4000/v1`

#### Scenario: El arnes de evaluacion desde el host sigue funcionando
- **WHEN** el arnes de evaluacion se ejecuta en modo real desde el host con `LITELLM_BASE_URL=http://localhost:4000/v1` en su entorno o en el `.env`
- **THEN** los agentes que el arnes ejecuta en el host llegan al proxy por esa URL del host
