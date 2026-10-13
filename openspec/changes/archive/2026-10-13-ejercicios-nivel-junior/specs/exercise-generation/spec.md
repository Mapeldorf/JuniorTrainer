# Spec Delta

## ADDED Requirements

### Requirement: Nivel junior de los ejercicios candidatos
El sistema SHALL producir candidatos resolubles por un desarrollador junior recien incorporado a un proyecto: cada candidato SHALL tratar un unico concepto y SHALL ser resoluble con el enunciado y el codigo de apoyo que se le entregan, sin pedir redisenos, refactors, cambios en varios ficheros ni decisiones de arquitectura.

#### Scenario: Candidato de tipo knowledge
- **WHEN** una generacion de tipo `knowledge` llega a Ready
- **THEN** cada candidato pregunta por un unico concepto de las tecnologias de la generacion, respondible sin consultar nada mas que lo que se entrega con el ejercicio

#### Scenario: Candidato de tipo debug
- **WHEN** una generacion de tipo `debug` llega a Ready
- **THEN** cada candidato pide encontrar y corregir un unico fallo dentro del codigo de apoyo que se entrega, sin pedir reescribir ni reorganizar el resto

#### Scenario: Un candidato pediria rediseno o varios pasos
- **WHEN** el agente de ejercicios redacta un candidato que exigiria redisenar, refactorizar o recorrer varios ficheros
- **THEN** ese candidato no se devuelve como resultado de la generacion

### Requirement: Longitud maxima del enunciado
El sistema SHALL limitar el enunciado de cada candidato a 50 palabras como maximo, contando como palabra cada secuencia de caracteres separada por espacios en blanco. El codigo de apoyo y la respuesta esperada no cuentan para ese limite.

#### Scenario: Enunciados de una generacion lista
- **WHEN** una generacion llega a Ready con sus candidatos
- **THEN** el enunciado de cada candidato tiene 50 palabras o menos

#### Scenario: Un enunciado se pasa del limite
- **WHEN** al redactar los candidatos alguno sale con un enunciado de mas de 50 palabras
- **THEN** se vuelven a pedir los candidatos indicando que acorten los enunciados que se pasaban, una sola vez

#### Scenario: El enunciado sigue pasandose tras el segundo intento
- **WHEN** tras ese segundo intento algun enunciado sigue teniendo mas de 50 palabras
- **THEN** la tarea del agente de ejercicios se da por fallida y la generacion queda en estado de error, sin devolver candidatos que incumplan el limite

### Requirement: Codigo de apoyo acotado
El sistema SHALL acotar el codigo de apoyo de cada candidato a un unico fragmento breve de un solo fichero, y SHALL dejarlo vacio en los candidatos de tipo `knowledge` que se entienden sin codigo. En los candidatos de tipo `debug` el codigo de apoyo SHALL contener exactamente un fallo introducido a proposito.

#### Scenario: Candidato knowledge que no necesita codigo
- **WHEN** un candidato de tipo `knowledge` se entiende solo con su enunciado
- **THEN** su codigo de apoyo se devuelve vacio

#### Scenario: Candidato debug con su codigo de apoyo
- **WHEN** una generacion de tipo `debug` llega a Ready
- **THEN** cada candidato trae un unico fragmento de un solo fichero, con exactamente un fallo introducido a proposito
