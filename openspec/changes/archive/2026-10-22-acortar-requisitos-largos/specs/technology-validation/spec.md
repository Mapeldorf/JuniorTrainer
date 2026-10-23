# Spec Delta

## MODIFIED Requirements

### Requirement: Validacion de tecnologias como puerta previa a la generacion
El sistema SHALL validar, antes de invocar a los agentes de entrada (web, codigo y ejercicios), que las tecnologias introducidas son tecnologias relacionadas con la programacion, mediante un agente validador dedicado, y SHALL continuar con la generacion unicamente si el validador da un veredicto afirmativo.

#### Scenario: Tecnologias validas
- **WHEN** se inicia una generacion cuyas tecnologias son todas tecnologias de programacion reconocibles
- **THEN** el validador da un veredicto afirmativo y la generacion continua con los agentes de entrada

#### Scenario: Tecnologias no tecnologicas
- **WHEN** al menos una de las tecnologias introducidas no es una tecnologia de programacion
- **THEN** el validador rechaza la entrada, la generacion queda en estado de error y no se invoca a ningun agente de entrada

#### Scenario: Tecnologia ya existente en el catalogo
- **WHEN** se inicia una generacion con una tecnologia que ya esta en el catalogo con ese mismo nombre, o que el validador consideraria una variante semantica de una tecnologia ya existente
- **THEN** el validador no la rechaza por ese motivo, y la generacion continua si la entrada es una tecnologia de programacion reconocible
- **AND** en este contexto el validador comprueba unicamente que cada entrada es una tecnologia de programacion, sin compararla contra el catalogo de tecnologias existentes
