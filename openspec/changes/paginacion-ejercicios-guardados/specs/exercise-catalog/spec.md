# Spec Delta

## MODIFIED Requirements

### Requirement: Listar y buscar ejercicios definitivos
El sistema SHALL permitir a un tech lead listar los ejercicios definitivos (`saved = true`, no eliminados), filtrables por tipo y buscables por texto en el nombre o en el enunciado, incluyendo para cada uno las tecnologias y el repositorio de la generacion de la que proviene, independientemente de si esa generacion sigue pendiente o ya esta cerrada (`done`), y en cuantos bloques de ejercicios esta incluido actualmente. El listado SHALL poder paginarse indicando una pagina y un tamano de pagina, y en ese caso SHALL devolver ademas el total de ejercicios coincidentes con los filtros aplicados.

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
- **THEN** sus tecnologias y repositorio siguen incluyendose en el listado de definitivos

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

## ADDED Requirements

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