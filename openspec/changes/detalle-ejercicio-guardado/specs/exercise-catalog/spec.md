# Spec Delta

## ADDED Requirements

### Requirement: Consultar el detalle de un ejercicio guardado en la interfaz

La pantalla de ejercicios guardados SHALL ofrecer, en cada ejercicio del listado, una accion "Ver" que abra un panel de detalle con el contenido completo del ejercicio seleccionado (nombre, tipo, tecnologias, repositorio, enunciado, bloques de codigo y respuesta esperada), en modo de solo lectura. El panel SHALL poder cerrarse y no SHALL modificar el ejercicio.

#### Scenario: Abrir el detalle de un ejercicio guardado

- **WHEN** un tech lead pulsa la accion "Ver" de un ejercicio del listado de guardados
- **THEN** se abre un panel de detalle con el nombre, el tipo, las tecnologias, el repositorio, el enunciado, los bloques de codigo y la respuesta esperada de ese ejercicio

#### Scenario: El detalle no modifica el ejercicio

- **WHEN** un tech lead abre y cierra el detalle de un ejercicio guardado
- **THEN** el ejercicio permanece sin cambios y sigue apareciendo igual en el listado

#### Scenario: Cerrar el detalle

- **WHEN** un tech lead cierra el panel de detalle
- **THEN** el panel deja de mostrarse y la pantalla vuelve al listado de guardados

#### Scenario: Ejercicio sin respuesta esperada

- **WHEN** un tech lead abre el detalle de un ejercicio guardado que no tiene respuesta esperada
- **THEN** el panel indica que no hay respuesta esperada en lugar de mostrar un valor vacio

#### Scenario: Cerrar el detalle con el teclado

- **WHEN** el panel de detalle esta abierto y el tech lead pulsa Escape
- **THEN** el panel se cierra