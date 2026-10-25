# Spec Delta

## ADDED Requirements

### Requirement: Umbrales de calidad y gate
El sistema SHALL mantener en el repositorio una tabla de umbrales de las metricas de la
suite, editable y ajustable por quien opera el sistema, y SHALL poder ejecutar el modo
real en un modo bloqueante que termine con codigo distinto de cero si alguna metrica con
casos incumple su umbral, nombrandola; y SHALL no evaluar las metricas sin casos,
informandolas aparte.

#### Scenario: Umbral incumplido
- **WHEN** una metrica con casos queda por debajo de su umbral (o por encima, si el umbral es un maximo) en modo bloqueante
- **THEN** la ejecucion termina con codigo distinto de cero y nombra la metrica, su valor y su umbral

#### Scenario: Todo dentro de umbral
- **WHEN** todas las metricas con casos cumplen su umbral
- **THEN** la ejecucion termina con codigo cero

#### Scenario: Metrica sin casos
- **WHEN** una metrica no tiene casos
- **THEN** no se evalua contra su umbral y se informa como no evaluada, no como incumplida

#### Scenario: Modo bloqueante solo en real
- **WHEN** se pide el modo bloqueante fuera del modo real
- **THEN** la ejecucion lo rechaza antes de evaluar ningun caso

#### Scenario: Umbrales como dato
- **WHEN** se cambia un umbral en la tabla
- **THEN** el gate lo refleja sin tocar el codigo del arnes

#### Scenario: El modo real sin gate no bloquea
- **WHEN** se ejecuta el modo real sin el modo bloqueante
- **THEN** la ejecucion informa las metricas y termina con codigo cero