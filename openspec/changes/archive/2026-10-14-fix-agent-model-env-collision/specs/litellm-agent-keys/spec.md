# Spec Delta

## ADDED Requirements

### Requirement: Resolucion de modelo logico aislada de la configuracion de LiteLLM
El sistema SHALL resolver, en cada uno de los 5 agentes, el nombre del modelo logico que envia a LiteLLM (`generator`, `evaluator` o `reviewer`, segun corresponda) de forma fija, sin leerlo de ninguna variable de entorno que `infra/litellm/config.yaml` tambien use para resolver el proveedor real detras de ese modelo logico.

#### Scenario: El agente envia el alias logico, no el nombre de proveedor
- **WHEN** cualquiera de los 5 agentes construye una llamada al proxy de LiteLLM
- **THEN** el campo `model` de esa llamada es el alias logico fijo del agente (`generator`, `evaluator` o `reviewer`)
- **AND** ese valor no cambia aunque la variable de entorno que LiteLLM usa para resolver el proveedor real (`GENERATOR_MODEL`/`EVALUATOR_MODEL`/`REVIEWER_MODEL`) este presente en el entorno del agente

#### Scenario: La llamada respeta la restriccion de modelo de la virtual key
- **WHEN** un agente con una virtual key restringida a su modelo logico realiza una llamada real a LiteLLM
- **THEN** LiteLLM la atiende con normalidad (no la rechaza con `403 key_model_access_denied`)
