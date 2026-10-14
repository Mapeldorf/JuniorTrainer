# Spec Delta

## ADDED Requirements

### Requirement: Validacion redundante de owner/repo en el agente de codigo
El agente de codigo SHALL validar `owner` y `repo` contra la misma expresion que exige el requisito "Referencia de entrada del repositorio" (solo caracteres alfanumericos y guiones, sin `/`, `..` ni espacios) antes de construir cualquier URL de la API de GitHub, con independencia de que el backend ya los haya validado al iniciar la generacion.

#### Scenario: El agente de codigo rechaza un owner/repo invalido aunque lo reciba directamente
- **WHEN** el agente de codigo recibe una tarea con `owner` o `repo` que no cumple la expresion permitida, sin pasar por la validacion del backend
- **THEN** el agente SHALL rechazar la tarea con un error claro y SHALL NOT construir ninguna URL de la API de GitHub con ese valor

#### Scenario: Una referencia valida se procesa con normalidad
- **WHEN** el agente de codigo recibe una tarea con `owner` y `repo` que cumplen la expresion permitida
- **THEN** el agente continua la tarea con normalidad, igual que antes de este requisito
