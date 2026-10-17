# Spec Delta

## ADDED Requirements

### Requirement: Alta de tecnologías por el tech lead
El sistema SHALL permitir a un tech lead dar de alta una tecnología en el catálogo. El alta SHALL validarse con el agente validador y la tecnología SHALL guardarse solo si el veredicto es afirmativo, normalizando el nombre (recortando espacios sobrantes).

#### Scenario: Alta de una tecnología válida
- **WHEN** un tech lead da de alta una tecnología que el validador reconoce como tecnología de programación
- **THEN** la tecnología se guarda en el catálogo con su nombre normalizado y queda disponible para seleccionar en la generación

### Requirement: Rechazo del validador en el alta
Si el agente validador da un veredicto negativo, el sistema SHALL NOT guardar la tecnología y SHALL devolver la causa del rechazo.

#### Scenario: La tecnología no es de programación
- **WHEN** un tech lead da de alta una entrada que el validador no reconoce como tecnología de programación
- **THEN** la petición se rechaza con la causa, no se crea ninguna fila en el catálogo y la entrada no queda disponible

### Requirement: Fallo del validador es fatal en el alta
Si el agente validador falla o no responde, el sistema SHALL NOT guardar la tecnología y SHALL devolver un error, sin dar el alta por buena.

#### Scenario: El validador no responde
- **WHEN** el agente validador no responde dentro del límite o falla por cualquier causa durante un alta
- **THEN** la petición responde con un error y no se guarda ninguna tecnología

### Requirement: Rechazo de tecnologías duplicadas en el alta
El sistema SHALL rechazar dar de alta una tecnología que ya existe en el catálogo, comparando sin distinguir mayúsculas ni espacios sobrantes, y SHALL NOT crear una fila duplicada.

#### Scenario: Nombre ya existente
- **WHEN** un tech lead da de alta una tecnología cuyo nombre ya está en el catálogo
- **THEN** la petición se rechaza y el catálogo no cambia

#### Scenario: Variante de mayúsculas o espacios de un nombre existente
- **WHEN** un tech lead da de alta una tecnología que coincide con una existente salvo por mayúsculas o espacios sobrantes
- **THEN** la petición se rechaza y el catálogo no cambia

### Requirement: Permiso de alta del catálogo
El alta de tecnologías SHALL estar reservada al tech lead; cualquier otro rol SHALL recibir una respuesta de acceso denegado y el catálogo SHALL NOT cambiar.

#### Scenario: Un alumno intenta dar de alta una tecnología
- **WHEN** un usuario con `role = student` intenta dar de alta una tecnología
- **THEN** la petición responde 403 y el catálogo no cambia

### Requirement: Interfaz de alta de tecnologías
La aplicación SHALL ofrecer al tech lead un formulario para dar de alta una tecnología, SHALL mostrar el resultado del alta (éxito, rechazo del validador o duplicado) y SHALL NOT exigir recargar la aplicación para que la nueva tecnología esté disponible.

#### Scenario: Alta correcta desde la interfaz
- **WHEN** el tech lead registra una tecnología válida desde el formulario de alta
- **THEN** la interfaz confirma el alta y la tecnología pasa a estar disponible en el formulario de generación

#### Scenario: Alta rechazada por el validador
- **WHEN** el tech lead registra una entrada que el validador rechaza
- **THEN** la interfaz muestra el motivo del rechazo y la tecnología no aparece como disponible

#### Scenario: Alta de un duplicado
- **WHEN** el tech lead registra una tecnología que ya existe en el catálogo
- **THEN** la interfaz muestra que ya existe y el catálogo no cambia

#### Scenario: Alta sin nombre
- **WHEN** el tech lead intenta registrar una tecnología sin escribir ningún nombre
- **THEN** el formulario no permite enviar el alta