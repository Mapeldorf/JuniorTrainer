# Spec Delta

## Purpose

Medir la calidad pedagógica del contenido generado —lo que las métricas deterministas
no pueden— con un juez LLM offline de rúbrica acotada, calibrado contra puntuaciones
humanas, para detectar cuándo un cambio de prompt o de modelo degrada el contenido
aunque el contrato de salida siga cumpliéndose.

## ADDED Requirements

### Requirement: Juicio offline con rubrica sobre un modelo distinto
El sistema SHALL puntuar ejercicios con un juez LLM **offline** —sin formar parte del
flujo de produccion ni abrir conexion con la base de datos—, aplicando una rubrica de
criterios acotados con justificacion obligatoria y salida JSON validada, y usando un
modelo **distinto** de los cuatro roles de produccion, configurable por variable de
entorno sin modificar el codigo de los agentes.

#### Scenario: Modelo distinto de produccion
- **WHEN** se ejecuta el juez
- **THEN** la llamada va por LiteLLM al alias del juez, resuelto por variable de entorno, y el informe registra el modelo usado

#### Scenario: Salida con la rubrica
- **WHEN** el juez puntua un ejercicio
- **THEN** el resultado trae una puntuacion por cada criterio aplicable y una justificacion no vacia

#### Scenario: Criterio que no aplica
- **WHEN** el ejercicio es de tipo `knowledge`
- **THEN** el criterio de calidad del fallo se informa como no aplicable, no como cero

#### Scenario: Salida invalida
- **WHEN** el juez no devuelve JSON valido con la rubrica esperada
- **THEN** se reintenta una sola vez y, si vuelve a fallar, el ejercicio cuenta como no juzgado y no como puntuacion

#### Scenario: Sin escrituras
- **WHEN** se ejecuta el juez
- **THEN** no se escribe en la base de datos ni se modifica ningun dato de la aplicacion

### Requirement: Conjunto de calibracion versionado y puntuacion humana separada
El sistema SHALL mantener en el repositorio un conjunto de ejercicios a juzgar y un
fichero aparte con las puntuaciones humanas sobre los mismos ejercicios, de modo que el
humano puntue sin conocer la puntuacion del juez.

#### Scenario: Conjunto a juzgar
- **WHEN** se carga el conjunto del juez
- **THEN** cada ejercicio lleva un identificador unico y su tipo, enunciado, codigo de apoyo y respuesta esperada

#### Scenario: Puntuacion humana separada
- **WHEN** se ejecuta la calibracion
- **THEN** las puntuaciones humanas se leen de un fichero distinto del conjunto a juzgar

#### Scenario: Caso mal formado
- **WHEN** un ejercicio del conjunto carece de un campo obligatorio
- **THEN** la carga falla indicando el caso y el campo, sin llamar a ningun modelo

### Requirement: Calibracion contra el humano
El sistema SHALL medir la concordancia entre las puntuaciones del juez y las humanas por
criterio mediante el coeficiente kappa de Cohen, e informar el numero de casos que la
respaldan.

#### Scenario: Concordancia por criterio
- **WHEN** se comparan las puntuaciones del juez con las humanas
- **THEN** el informe da un kappa por criterio y un valor global

#### Scenario: Puntuacion humana incompleta
- **WHEN** falta la puntuacion humana de un ejercicio
- **THEN** ese ejercicio se excluye de la calibracion y el informe lo indica, sin suponer un valor

#### Scenario: Concordancia baja
- **WHEN** el kappa de un criterio es bajo
- **THEN** la accion documentada es corregir la rubrica, no el resultado

### Requirement: Informe del juez
El sistema SHALL producir en cada ejecucion un informe estructurado y un resumen legible
con la rubrica, el modelo juez, las puntuaciones por ejercicio y el resultado de la
calibracion, sin bloquear la ejecucion por una puntuacion baja.

#### Scenario: Informe generado
- **WHEN** termina una ejecucion del juez
- **THEN** existe un informe con el modelo usado, las puntuaciones por ejercicio y, si hay puntuaciones humanas, la calibracion

#### Scenario: Sin calibracion
- **WHEN** se ejecuta el juez sin puntuaciones humanas
- **THEN** el informe da las puntuaciones e informa la calibracion como no disponible

#### Scenario: Una puntuacion baja no bloquea
- **WHEN** la media de un criterio queda por debajo de lo deseable
- **THEN** la ejecucion informa el valor y termina con codigo cero

### Requirement: El juez no sustituye la aprobacion humana
El sistema SHALL declarar que el juez es un instrumento de regresion y que no aprueba ni
rechaza contenido en produccion: la aprobacion de un ejercicio sigue siendo humana.

#### Scenario: Limite declarado
- **WHEN** se documenta el juez en el repositorio
- **THEN** se dice explicitamente que no sustituye la aprobacion del tech lead