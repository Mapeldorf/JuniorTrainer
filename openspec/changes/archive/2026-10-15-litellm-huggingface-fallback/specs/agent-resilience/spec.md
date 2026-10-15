# Spec Delta

## ADDED Requirements

### Requirement: Fallback automatico a un proveedor alternativo
El proxy LiteLLM SHALL reintentar automaticamente, contra un modelo de un proveedor alternativo, toda llamada que falle al modelo logico principal, antes de devolver el error al agente que la origino.

#### Scenario: El modelo principal falla
- **WHEN** una llamada de LiteLLM al modelo principal de un modelo logico falla
- **THEN** LiteLLM SHALL reintentar la misma llamada contra el modelo de fallback configurado para ese modelo logico, sin que el agente tenga que solicitarlo

#### Scenario: El modelo principal responde con normalidad
- **WHEN** el modelo principal responde correctamente
- **THEN** la llamada se completa con normalidad, sin invocar al modelo de fallback

### Requirement: El fallback respeta la restriccion de modelo por virtual key
Una virtual key SOLO SHALL poder completar una llamada de fallback si el modelo de fallback correspondiente esta incluido en su lista de modelos permitidos.

#### Scenario: La virtual key tiene permitido su modelo de fallback
- **WHEN** la llamada de un agente a su modelo principal falla y LiteLLM reintenta contra el modelo de fallback que esa virtual key tiene permitido
- **THEN** la llamada de fallback se completa con normalidad

#### Scenario: Una virtual key no puede usar el fallback de otro agente
- **WHEN** se intenta usar una virtual key para llamar directamente al modelo de fallback de un modelo logico distinto del suyo
- **THEN** LiteLLM SHALL rechazar la llamada, igual que ya rechaza una llamada directa a cualquier otro modelo que esa key no tenga permitido
