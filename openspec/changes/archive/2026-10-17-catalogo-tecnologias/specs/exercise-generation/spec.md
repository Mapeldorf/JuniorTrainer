# Spec Delta

## ADDED Requirements

### Requirement: Tecnologías de la generación limitadas al catálogo
El sistema SHALL aceptar como tecnologías de una generación únicamente tecnologías presentes en el catálogo canónico, SHALL normalizar cada tecnología al nombre canónico del catálogo antes de usarla, y SHALL rechazar la petición sin crear ninguna generación si alguna tecnología no pertenece al catálogo.

#### Scenario: Tecnología del catálogo
- **WHEN** se inicia una generación con tecnologías que existen en el catálogo
- **THEN** la petición se acepta y la generación guarda los nombres canónicos del catálogo

#### Scenario: Tecnología fuera del catálogo
- **WHEN** se inicia una generación con una tecnología que no existe en el catálogo
- **THEN** la petición se rechaza con un error de validación y no se crea ninguna generación

#### Scenario: Variante de un nombre canónico
- **WHEN** se inicia una generación con una tecnología que coincide con un nombre del catálogo salvo por mayúsculas o espacios sobrantes
- **THEN** la petición se acepta y esa tecnología se guarda con el nombre canónico del catálogo

### Requirement: Selección determinista de tecnologías en el formulario
El formulario de generación de ejercicios SHALL ofrecer las tecnologías como una selección múltiple desde el catálogo, con una búsqueda que filtra dentro del catálogo, y SHALL NOT ofrecer ningún campo para introducir tecnologías de texto libre.

#### Scenario: Seleccionar tecnologías del catálogo
- **WHEN** el tech lead abre el formulario de generación
- **THEN** puede seleccionar las tecnologías de entre las del catálogo y no existe un campo de texto libre para añadir tecnologías

#### Scenario: Buscar dentro del catálogo
- **WHEN** el tech lead escribe en el selector de tecnologías para filtrar
- **THEN** solo se muestran las tecnologías del catálogo que coinciden con el texto escrito

#### Scenario: Generar sin ninguna tecnología seleccionada
- **WHEN** el tech lead intenta generar sin haber seleccionado ninguna tecnología del catálogo
- **THEN** el formulario no permite iniciar la generación