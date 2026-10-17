# Design

## Context

Hoy `GET /exercises` (`backend/app/routers/exercises.py`) selecciona todos los ejercicios definitivos con Supabase, los ordena por `created_at desc` y devuelve un array plano `list[SavedExerciseListItem]`. Lo consumen dos pantallas via `GenerationsApiService.listSaved`: `/ejercicios` (tabla de guardados) y `bloque-editar` (catálogo para componer un bloque). El frontend es Angular 22 standalone con Tailwind v4 y sin libreria de componentes: los controles se escriben a mano con utilidades y tokens del tema oscuro (`focus-ring`, `btn`, `input`, colores `border`/`muted`/`content`).

Ver proposal.md - Why para la motivacion.

## Goals / Non-Goals

**Goals:**
- Paginar en el servidor el listado de guardados, con total de coincidencias, sin cargar todo el catalogo.
- Que `/ejercicios` muestre 10 por pagina con un control numerado Anterior/Siguiente.
- No romper el uso de `GET /exercises` por parte de la edicion de bloques.

**Non-Goals:**
- Paginar la lista de generaciones pendientes ni otros listados.
- Busqueda/filtrado en el servidor distinto del ya existente (`type`, `q`).
- Elipsis / truncado de numeros de pagina para catalogos muy largos (se muestran todos los numeros).

## Decisions

**D1 - Paginacion en el servidor con Supabase `range` + `count` exacto.**
Se aplican los mismos filtros (`saved=true`, `deleted_at is null`, `type`, `q`) y la misma ordenacion (`created_at desc`) tanto al conteo como a la pagina. Se pide el total con `select(fields, count="exact")` (devuelve `result.count`) y se corta la pagina con `.range(offset, offset + page_size - 1)`, con `offset = (page - 1) * page_size`. Alternativa descartada: paginar en el cliente (traeria todo el catalogo, justo lo que se quiere evitar).

**D2 - La respuesta pasa a ser un sobre `{ items, total, page, page_size }`.**
Nuevo esquema `SavedExercisesPage` en `backend/app/schemas/exercise.py` y su espejo TypeScript. Alternativas descartadas: (a) mantener el array plano y enviar el total por cabecera `X-Total-Count` (contrato oculto, mas fragil de tipar y testear); (b) endpoint nuevo solo para la pantalla (duplicaria consulta y logica de filtros). El cambio de forma de la respuesta es la parte **BREAKING** del proposal y obliga a tocar los dos consumidores frontend.

**D3 - Parametros `page` y `page_size`, con `page_size` opcional que preserva el comportamiento actual.**
`page` es 1-based con valor por defecto 1 (se rechaza con 422 si es < 1). `page_size` es opcional: si se **omite**, se devuelven todos los coincidentes (`items` con todas las filas, `page=1`, `page_size=total`), que es exactamente lo que necesita `bloque-editar`; si se informa, se valida `>= 1` y se limita a un maximo (100) para acotar el trabajo por peticion. Asi la ruta mantiene un unico contrato y la edicion de bloques no necesita paginar.

**D4 - `bloque-editar` se adapta leyendo `items` y sin pasar paginacion.**
Su `cargarCatalogo()` sigue llamando a `listSaved({ type, q })` (sin `page_size`) y solo cambia `items` -> `response.items`. No cambia su comportamiento observable (sigue viendo todo el catalogo filtrado).

**D5 - Componente de paginacion propio, patron "Pagination" de Tailwind UI.**
Se crea un componente standalone reutilizable en `frontend/src/app/core/` (junto a `confirm-dialog`), puramente presentacional: recibe la pagina actual y el numero total de paginas (`input`), y emite `pageChange` al pulsar un numero, Anterior o Siguiente. Se construye con utilidades Tailwind del tema (superficie, `border`, `text-content`/`text-muted`, `focus-ring`, estado deshabilitado en los extremos) en vez de una libreria: el proyecto no usa ninguna (ver `package.json`) y su `frontend-ui-theme` exige el lenguaje visual propio. El patron elegido es el numerado con Anterior/Siguiente de Tailwind UI (elegido por el usuario); no se añade elipsis (fuera de alcance).

**D6 - Estado de paginacion en `EjerciciosComponent`.**
Signals `page = 1`, `pageSize = 10` (constante) y `total`; `totalPages = ceil(total / pageSize)`. `loadSaved()` envia `page` y `page_size`. `onFilterTypeChange` y `onSearchTextChange` resetean `page` a 1 antes de recargar. Tras `eliminar()`, si la pagina actual queda vacia y no es la primera, se retrocede una pagina antes de recargar.

**D7 - `listSaved` mantiene el nombre y suma `page`/`page_size` a sus filtros.**
`ListSavedExercisesFilters` gana `page?` y `page_size?`, y `listSaved` pasa de devolver `SavedExerciseListItem[]` a `SavedExercisesPage`. Renombrar el metodo o meter uno nuevo añadiria superficie sin beneficio; los dos consumidores se actualizan en el mismo cambio.

## Risks / Trade-offs

- [Cambio de forma de la respuesta rompe a los consumidores] -> Se localizaron los dos unicos usos (`grep listSaved`): `/ejercicios` y `bloque-editar`; ambos y sus tests se actualizan en este cambio, y el script de verificacion de backend cubre el nuevo contrato.
- [Eliminar el ultimo elemento de una pagina deja una pagina vacia] -> `EjerciciosComponent` retrocede de pagina antes de recargar cuando detecta el caso (escenario "Eliminar el ultimo ejercicio de una pagina").
- [Conteo y pagina podrian discrepar si cambia el catalogo entre ambas consultas] -> Se usa la misma query y filtros con `count="exact"`; una discrepancia puntual solo afecta al numero de paginas mostrado, no a la integridad de los datos.
- [`page_size` ausente devuelve todo: un catalogo grande sigue siendo una respuesta grande para `bloque-editar`] -> Aceptado: es el comportamiento actual y la edicion de bloques necesita el catalogo completo; se podra paginar ese caso en un cambio futuro si hiciera falta.

## Migration Plan

- Sin migraciones de base de datos.
- Despliegue: backend y frontend deben ir juntos porque el contrato de `GET /exercises` cambia en ambos lados; publicar backend y frontend en el mismo release.
- Rollback: revertir el cambio de ambos artefactos a la vez (no hay estado persistido que migrar).

## Open Questions

- Ninguna que cambie el alcance, los specs o el desglose de tareas. El tope de `page_size` (100) y el tamaño de pagina de la interfaz (10) quedan fijados en este diseno.