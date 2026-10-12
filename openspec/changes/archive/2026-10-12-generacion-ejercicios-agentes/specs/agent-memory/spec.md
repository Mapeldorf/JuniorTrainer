# Spec Delta

## Purpose

Define el comportamiento observable de la memoria de los agentes de generacion entre tareas: que no repitan busquedas, lecturas de fichero ni temas de ejercicio ya vistos para la misma entrada, y que una fuente de memoria caida nunca bloquee la generacion.

## ADDED Requirements

### Requirement: El agente web no repite busquedas para las mismas tecnologias
El sistema SHALL reutilizar el resumen y las fuentes de una busqueda previa cuando una generacion posterior pide las mismas tecnologias, sin volver a llamar a la herramienta de busqueda web.

#### Scenario: Segunda generacion con las mismas tecnologias
- **WHEN** se lanza una generacion con tecnologias ya buscadas en una generacion anterior
- **THEN** el agente web devuelve el resumen guardado y no realiza ninguna llamada a la herramienta de busqueda web

#### Scenario: Primera vez con esas tecnologias
- **WHEN** se lanza una generacion con tecnologias que no se han buscado antes
- **THEN** el agente web llama a la herramienta de busqueda web y guarda el resultado para una proxima vez

### Requirement: El agente de codigo no relee el mismo repositorio
El sistema SHALL reutilizar el resumen, las tecnologias detectadas y los fragmentos de un repositorio ya procesado con las mismas tecnologias, sin volver a leer sus ficheros.

#### Scenario: Segunda generacion con el mismo repositorio y tecnologias
- **WHEN** se lanza una generacion con un repositorio y tecnologias ya procesados antes
- **THEN** el agente de codigo devuelve el resultado guardado y no lee ningun fichero del repositorio

#### Scenario: Mismo repositorio, tecnologias distintas
- **WHEN** se lanza una generacion con un repositorio ya procesado pero con tecnologias distintas a las de la vez anterior
- **THEN** el agente de codigo vuelve a leer el repositorio para esas tecnologias

### Requirement: El agente de ejercicios no repite temas ya propuestos
El sistema SHALL evitar que el agente de ejercicios proponga un ejercicio sobre el mismo tema que uno ya propuesto antes para el mismo tipo, usando su propio historial ademas de los ejercicios guardados.

#### Scenario: Generaciones repetidas del mismo tipo
- **WHEN** se piden varias generaciones seguidas del mismo tipo de ejercicio
- **THEN** los enunciados candidatos de cada nueva generacion no repiten el tema de uno ya propuesto antes para ese tipo

### Requirement: Un acierto de memoria no consume los limites de la tarea
El sistema SHALL contar una respuesta servida desde memoria como tarea completada sin gastar el limite de busquedas del agente web ni el de ficheros leidos del agente de codigo.

#### Scenario: Acierto de memoria en el agente web
- **WHEN** el agente web responde desde memoria
- **THEN** no se descuenta ninguna busqueda de su limite de hasta 5 por tarea

### Requirement: Un acierto de memoria queda marcado en la traza
El sistema SHALL marcar en la traza de Langfuse de la tarea correspondiente que la respuesta vino de memoria.

#### Scenario: Acierto de memoria en cualquier agente de generacion
- **WHEN** un agente de generacion responde desde memoria
- **THEN** su traza de Langfuse para esa tarea queda marcada como acierto de memoria

### Requirement: Una memoria caida no bloquea la generacion
El sistema SHALL continuar la generacion sin memoria si una lectura falla, tratandola como si no hubiera entrada guardada, y SHALL ignorar sin interrumpir la generacion el fallo de una escritura a memoria.

#### Scenario: Falla una lectura de memoria
- **WHEN** la consulta a memoria de un agente falla
- **THEN** el agente actua como si no hubiera encontrado nada guardado y continua su tarea con normalidad

#### Scenario: Falla una escritura de memoria
- **WHEN** un agente no consigue guardar su resultado en memoria tras completarse
- **THEN** la generacion no se ve afectada por ese fallo

### Requirement: La memoria no guarda datos de alumnos
El sistema SHALL excluir de la memoria de los agentes de generacion cualquier respuesta, nombre o email de alumno.

#### Scenario: Revisar lo que guarda la memoria de los agentes de generacion
- **WHEN** se inspecciona lo que la memoria de los agentes de generacion ha guardado
- **THEN** no aparece ninguna respuesta, nombre ni email de alumno
