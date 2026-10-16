# Spec Delta

## ADDED Requirements

### Requirement: Entrada de validacion de tecnologias no se registra en claro en Langfuse
El sistema SHALL evitar que el texto de las tecnologias introducidas por el usuario llegue en claro al backend de tracing externo en la llamada del agente validador al LLM, donde ese texto se interpola en el prompt.

#### Scenario: Validacion de tecnologias
- **WHEN** el agente validador llama al LLM para decidir si las tecnologias introducidas son tecnologias de programacion
- **THEN** el prompt de esa llamada SHALL NOT aparecer en claro en el backend de tracing externo

#### Scenario: La traza del validador sigue siendo util
- **WHEN** se consulta en el backend de tracing externo una traza de una llamada del validador
- **THEN** el coste, la latencia, el numero de tokens, el modelo usado y si tuvo exito o fallo SHALL seguir siendo visibles, aunque el contenido del prompt no lo sea
