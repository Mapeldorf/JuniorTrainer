# Spec Delta

## ADDED Requirements

### Requirement: Control del esfuerzo de razonamiento en modo real
El sistema SHALL permitir fijar, **solo en modo real**, el esfuerzo de razonamiento
de los modelos —un nivel de esfuerzo, un tope de tokens de razonamiento, o
desactivado— inyectando el parametro correspondiente en la llamada al modelo sin
modificar el codigo de los agentes y sin pisar lo que el agente ya envia en esa
llamada, y SHALL registrar en el informe el ajuste usado para poder comparar coste y
calidad entre ajustes.

#### Scenario: Ajuste por nivel de esfuerzo
- **WHEN** se ejecuta la evaluacion en modo real indicando un nivel de esfuerzo de razonamiento
- **THEN** cada llamada al modelo lleva ese nivel en el parametro de razonamiento, junto a los datos que el agente ya pone en la llamada, y el informe registra el ajuste

#### Scenario: Ajuste por tope de tokens
- **WHEN** se ejecuta en modo real indicando un tope de tokens de razonamiento
- **THEN** cada llamada al modelo lleva ese tope en el parametro de razonamiento y el informe registra el ajuste

#### Scenario: Razonamiento desactivado
- **WHEN** se ejecuta en modo real indicando el razonamiento desactivado
- **THEN** cada llamada al modelo pide que el razonamiento este desactivado y el informe registra el ajuste

#### Scenario: Ajuste invalido
- **WHEN** se indica un ajuste de razonamiento que no es un nivel conocido, un tope de tokens positivo ni la desactivacion
- **THEN** la ejecucion termina con error antes de llamar a ningun modelo

#### Scenario: Ajuste rechazado en modo simulado
- **WHEN** se indica un ajuste de razonamiento sin estar en modo real
- **THEN** la ejecucion lo rechaza, porque el doble guionizado no llama a ningun proveedor y el ajuste no tendria efecto

#### Scenario: Baseline sin ajuste
- **WHEN** se ejecuta en modo real sin indicar ningun ajuste de razonamiento
- **THEN** no se inyecta ningun parametro de razonamiento y el informe registra que no se fijo ninguno
