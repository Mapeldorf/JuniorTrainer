# Spec Delta

## MODIFIED Requirements

### Requirement: El agente de ejercicios no repite temas ya propuestos
El sistema SHALL evitar que el agente de ejercicios proponga un ejercicio sobre el mismo tema que uno de los 200 ejercicios mas recientes ya propuestos para el mismo tipo, consultando en base de datos los que estan guardados (`saved = true`) o eliminados (`deleted_at` no nulo), sin mantener ningun historial propio del agente.

#### Scenario: Generaciones repetidas del mismo tipo
- **WHEN** se piden varias generaciones seguidas del mismo tipo de ejercicio
- **THEN** los enunciados candidatos de cada nueva generacion no repiten el tema de ninguno de los 200 ejercicios guardados o eliminados mas recientes para ese tipo

#### Scenario: Un ejercicio eliminado no se vuelve a proponer
- **WHEN** un ejercicio de un tipo fue generado, aceptado y despues eliminado
- **THEN** una generacion posterior del mismo tipo recibe su enunciado en la lista de temas a evitar, igual que si siguiera guardado, mientras siga entre los 200 mas recientes de ese tipo
