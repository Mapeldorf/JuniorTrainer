# Spec Delta

## ADDED Requirements

### Requirement: Longitud maxima de la justificacion
El sistema SHALL limitar a 50 palabras como maximo la justificacion que se persiste con una respuesta evaluada, contando como palabra cada secuencia de caracteres separada por espacios en blanco. El limite SHALL aplicarse tanto a la justificacion propuesta al decidir el verdict como a la version revisada que finalmente se persiste.

#### Scenario: Respuesta evaluada como correcta
- **WHEN** un alumno envia una respuesta que se evalua como `correct`
- **THEN** la justificacion que se persiste tiene 50 palabras o menos

#### Scenario: Respuesta evaluada como incompleta o incorrecta
- **WHEN** un alumno envia una respuesta que se evalua como `incomplete` o `incorrect`
- **THEN** la justificacion que se persiste tiene 50 palabras o menos y senala igualmente que falta o que esta mal

#### Scenario: La justificacion propuesta se pasa del limite
- **WHEN** al evaluar una respuesta la justificacion propuesta sale con mas de 50 palabras
- **THEN** se vuelve a pedir una justificacion mas corta, una sola vez, antes de continuar con la revision

#### Scenario: La revision devuelve una justificacion mas larga que el limite
- **WHEN** la version revisada de la justificacion sale con mas de 50 palabras
- **THEN** se vuelve a pedir la revision acortandola, una sola vez, y no se persiste una justificacion que incumpla el limite

#### Scenario: La justificacion sigue pasandose tras el segundo intento
- **WHEN** tras ese segundo intento la justificacion sigue teniendo mas de 50 palabras
- **THEN** la evaluacion no puede completarse: no se persiste ninguna respuesta para ese ejercicio y el alumno recibe un error que le permite reintentar
