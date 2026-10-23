# Spec Delta

## MODIFIED Requirements

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
