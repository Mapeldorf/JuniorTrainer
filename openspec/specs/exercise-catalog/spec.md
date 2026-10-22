# exercise-catalog Specification

## Purpose

Define como un ejercicio generado pasa a ser definitivo, como se encuentra entre los definitivos para componer un bloque, y que efecto tiene eliminarlo de la app.

## Requirements

### Requirement: Guardar un ejercicio candidato como definitivo
El sistema SHALL permitir a un tech lead marcar como definitivo (`saved = true`) un ejercicio candidato (`saved = false`, no eliminado) de una generacion, opcionalmente sustituyendo su nombre y/o su respuesta esperada por unos editados en ese mismo momento; a partir de ese momento el ejercicio SHALL volverse inmutable salvo su `deleted_at`.

#### Scenario: Guardar un candidato
- **WHEN** un tech lead guarda un ejercicio candidato existente, no guardado y no eliminado
- **THEN** el ejercicio pasa a `saved = true` y queda disponible para anadirse a bloques

#### Scenario: Guardar un candidato con la respuesta esperada editada
- **WHEN** un tech lead guarda un ejercicio candidato indicando una respuesta esperada distinta a la generada
- **THEN** el ejercicio se guarda con la respuesta esperada indicada, no con la original

#### Scenario: Guardar un candidato con el nombre editado
- **WHEN** un tech lead guarda un ejercicio candidato indicando un nombre distinto al generado
- **THEN** el ejercicio se guarda con el nombre indicado, no con el original

#### Scenario: Intentar guardar un ejercicio ya guardado o eliminado
- **WHEN** se intenta guardar un ejercicio cuyo `saved` ya es `true`, o cuyo `deleted_at` no es nulo
- **THEN** la peticion se rechaza y el ejercicio no cambia

#### Scenario: Un alumno no puede guardar ejercicios
- **WHEN** un usuario con `role = student` intenta guardar un ejercicio candidato
- **THEN** la peticion responde 403 y el ejercicio no cambia

### Requirement: Listar y buscar ejercicios definitivos
El sistema SHALL permitir a un tech lead listar los ejercicios definitivos (`saved = true`, no eliminados), filtrables por tipo y buscables por texto en el nombre o en el enunciado. Cada ejercicio SHALL incluir las tecnologias y el repositorio de su generacion y en cuantos bloques esta incluido, y el listado SHALL poder paginarse devolviendo el total de coincidencias.

#### Scenario: Listar sin filtros
- **WHEN** un tech lead lista los ejercicios definitivos sin ningun filtro
- **THEN** devuelve todos los ejercicios con `saved = true` y `deleted_at` nulo, sin candidatos ni eliminados

#### Scenario: Filtrar por tipo
- **WHEN** un tech lead lista los ejercicios definitivos indicando un tipo (`knowledge` o `debug`)
- **THEN** devuelve solo los ejercicios definitivos de ese tipo

#### Scenario: Buscar por texto
- **WHEN** un tech lead lista los ejercicios definitivos indicando un texto de busqueda
- **THEN** devuelve solo los ejercicios definitivos cuyo nombre o enunciado contiene ese texto

#### Scenario: Buscar por texto en el nombre
- **WHEN** un tech lead lista los ejercicios definitivos indicando un texto que coincide con el nombre de alguno
- **THEN** devuelve esos ejercicios definitivos, aunque el texto no aparezca en su enunciado

#### Scenario: Buscar por texto en el enunciado
- **WHEN** un tech lead lista los ejercicios definitivos indicando un texto que coincide con el enunciado de alguno pero no con su nombre
- **THEN** devuelve esos ejercicios definitivos igualmente

#### Scenario: Un ejercicio guardado incluye las tecnologias y el repositorio de su generacion
- **WHEN** un tech lead lista los ejercicios definitivos
- **THEN** cada ejercicio incluye las tecnologias y el repositorio (si lo hubiera) de la generacion de la que proviene

#### Scenario: Las tecnologias y el repositorio se incluyen aunque la generacion ya este cerrada
- **WHEN** un ejercicio definitivo proviene de una generacion que ya esta en `done`
- **THEN** sus tecnologias y repositorio siguen incluyendose en el listado de definitivos, independientemente de si esa generacion sigue pendiente o ya esta cerrada

#### Scenario: Un ejercicio guardado indica en cuantos bloques esta
- **WHEN** un tech lead lista los ejercicios definitivos
- **THEN** cada ejercicio incluye en cuantos bloques de ejercicios esta incluido actualmente, aunque sea en ninguno

#### Scenario: Paginar el listado
- **WHEN** un tech lead lista los ejercicios definitivos indicando una pagina y un tamano de pagina
- **THEN** devuelve solo los ejercicios de esa pagina, en el mismo orden que sin paginar, junto con el total de ejercicios coincidentes

#### Scenario: Una pagina mas alla de la ultima devuelve una pagina vacia
- **WHEN** un tech lead pide una pagina posterior a la ultima existente
- **THEN** devuelve una lista de ejercicios vacia y el total sigue siendo el numero real de coincidencias

#### Scenario: La paginacion respeta los filtros
- **WHEN** un tech lead lista paginando y ademas indica un tipo o un texto de busqueda
- **THEN** el total y los ejercicios de la pagina corresponden solo a los que cumplen ese filtro

#### Scenario: Sin tamano de pagina el listado devuelve todos los coincidentes
- **WHEN** se lista los ejercicios definitivos sin indicar tamano de pagina
- **THEN** devuelve todos los ejercicios coincidentes, como antes de existir la paginacion

### Requirement: Eliminar logicamente un ejercicio definitivo
El sistema SHALL permitir a un tech lead eliminar un ejercicio definitivo marcando su `deleted_at`, de modo que deje de aparecer en el listado de definitivos y de poder anadirse a bloques nuevos, sin alterar los bloques que ya lo contengan ni las copias de asignacion ya creadas.

#### Scenario: Eliminar un ejercicio definitivo
- **WHEN** un tech lead elimina un ejercicio con `saved = true`
- **THEN** el ejercicio queda con `deleted_at` informado, deja de aparecer en el listado de definitivos, y la base de datos rechaza anadirlo a cualquier bloque nuevo

#### Scenario: Eliminar un ejercicio ya usado en bloques o asignaciones
- **WHEN** se elimina un ejercicio definitivo que ya forma parte de uno o mas bloques, o de copias de asignacion ya creadas
- **THEN** esos bloques y esas copias de asignacion no cambian

### Requirement: Paginar el listado de ejercicios guardados en la interfaz
La pantalla de ejercicios guardados SHALL mostrar los ejercicios en paginas de 10 elementos y SHALL ofrecer un control de paginacion numerado con acciones de pagina anterior y siguiente; al cambiar de pagina SHALL mostrar solo esa pagina, y al cambiar el filtro de tipo o el texto de busqueda SHALL volver a la primera pagina.

#### Scenario: Mostrar diez ejercicios por pagina
- **WHEN** un tech lead abre la pantalla de ejercicios guardados y hay mas de 10 coincidencias
- **THEN** la tabla muestra como maximo 10 ejercicios y el control de paginacion refleja que hay mas de una pagina

#### Scenario: Navegar entre paginas
- **WHEN** un tech lead usa el control de paginacion para ir a otra pagina
- **THEN** la tabla muestra los ejercicios de esa pagina y el control marca esa pagina como la actual

#### Scenario: Sin paginacion cuando hay una sola pagina
- **WHEN** hay 10 o menos ejercicios guardados que cumplen los filtros
- **THEN** no se muestra un control de paginacion con varias paginas

#### Scenario: Cambiar el filtro o la busqueda vuelve a la primera pagina
- **WHEN** un tech lead esta en una pagina posterior a la primera y cambia el tipo o el texto de busqueda
- **THEN** el listado se recarga mostrando la primera pagina de los resultados filtrados

#### Scenario: Eliminar el ultimo ejercicio de una pagina
- **WHEN** un tech lead elimina el unico ejercicio que quedaba en la pagina actual y la pagina deja de tener elementos
- **THEN** la pantalla muestra la pagina anterior (o la primera, si ya era la primera) con los ejercicios restantes

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
