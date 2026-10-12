# answer-evaluation Specification

## Purpose

Define como un alumno envia su respuesta a un ejercicio de su propia asignacion, como esa respuesta se evalua automaticamente contra la copia inmutable del ejercicio, y como se persiste el resultado (verdict y justificacion).

## Requirements

### Requirement: Enviar una respuesta a un ejercicio de la propia asignacion
El sistema SHALL permitir a un alumno enviar una respuesta a un ejercicio que forma parte de una asignacion suya, y SHALL rechazar el intento si el ejercicio no pertenece a ninguna asignacion de ese alumno.

#### Scenario: Enviar una respuesta valida
- **WHEN** un alumno envia una respuesta a un ejercicio de una de sus propias asignaciones
- **THEN** la respuesta queda evaluada y persistida, y el alumno recibe el resultado

#### Scenario: Responder un ejercicio que no esta en la propia asignacion
- **WHEN** un alumno intenta responder a un `exercise_id` que no forma parte de la copia de ninguna de sus asignaciones
- **THEN** la peticion se rechaza y no se crea ninguna respuesta

#### Scenario: Responder un ejercicio de la asignacion de otro alumno
- **WHEN** un alumno intenta responder usando el `assignment_id` de una asignacion que pertenece a otro alumno
- **THEN** la peticion se rechaza y no se crea ninguna respuesta

### Requirement: Un ejercicio de una asignacion solo se responde una vez
El sistema SHALL rechazar con un motivo identificable el intento de enviar una segunda respuesta al mismo ejercicio de la misma asignacion, sin modificar la respuesta ya registrada.

#### Scenario: Responder dos veces el mismo ejercicio
- **WHEN** un alumno envia una respuesta a un ejercicio de su asignacion que ya tiene una respuesta registrada
- **THEN** la peticion se rechaza identificando que ese ejercicio ya fue respondido, y la respuesta original no cambia

### Requirement: La evaluacion usa la copia de la asignacion, nunca el ejercicio original
El sistema SHALL evaluar la respuesta del alumno comparandola contra el enunciado y la respuesta esperada de la copia guardada en su propia asignacion, y ese resultado SHALL permanecer igual aunque el ejercicio original cambie de estado despues.

#### Scenario: El ejercicio original fue eliminado tras asignar el bloque
- **WHEN** un alumno responde a un ejercicio cuyo `exercise` original ya tiene `deleted_at` informado
- **THEN** la evaluacion se realiza igualmente contra el enunciado y la respuesta esperada de la copia de su asignacion

### Requirement: El resultado de la evaluacion incluye un verdict y una justificacion revisada
El sistema SHALL determinar, para cada respuesta evaluada, un verdict entre `correct`, `incomplete` o `incorrect`, junto con una justificacion que haya sido revisada antes de persistirse, y SHALL persistir la respuesta junto con ambos en la misma operacion.

#### Scenario: Respuesta evaluada como correcta
- **WHEN** la respuesta del alumno coincide con lo esperado para ese ejercicio
- **THEN** se persiste con verdict `correct` y una justificacion revisada

#### Scenario: Respuesta evaluada como incompleta o incorrecta
- **WHEN** la respuesta del alumno no coincide, total o parcialmente, con lo esperado para ese ejercicio
- **THEN** se persiste con el verdict (`incomplete` o `incorrect`) y una justificacion revisada que corresponde a ese veredicto

#### Scenario: La evaluacion no puede completarse
- **WHEN** el proceso de evaluacion de una respuesta no puede completarse (p.ej. un fallo al obtener el verdict o la justificacion revisada)
- **THEN** no se persiste ninguna respuesta para ese ejercicio y el alumno recibe un error que le permite reintentar
