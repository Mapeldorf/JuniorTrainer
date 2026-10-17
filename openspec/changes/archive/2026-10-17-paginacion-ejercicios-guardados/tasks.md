# Tasks

## 1. Backend: paginacion de `GET /exercises`

- [x] 1.1 Anadir el esquema `SavedExercisesPage` (`items: list[SavedExerciseListItem]`, `total: int`, `page: int`, `page_size: int`) en `backend/app/schemas/exercise.py` y exportarlo en `__all__`; verificar importando el modulo sin error.
- [x] 1.2 Anadir a `list_saved_exercises` los parametros opcionales `page` (default 1, 1-based) y `page_size` (default `None`, tope 100), y pedir el total con `count="exact"` sobre la misma query filtrada/ordenada; verificar que sin parametros devuelve todos los coincidentes con `total` igual al numero de filas.
- [x] 1.3 Aplicar el corte de pagina con `.range(offset, offset + page_size - 1)` cuando se informe `page_size`, y devolver el sobre `SavedExercisesPage`; verificar que una pagina intermedia devuelve exactamente `page_size` filas y el mismo `total`.
- [x] 1.4 Extender `backend/scripts/verify_ejercicios_tech_lead.py` para cubrir el listado paginado (pagina intermedia, ultima pagina, pagina fuera de rango vacia con `total` correcto, filtro `type`/`q` respetado, y sin `page_size` devuelve todo); verificar ejecutando `python -m scripts.verify_ejercicios_tech_lead`.

## 2. Frontend: contrato y servicio

- [x] 2.1 Anadir la interfaz `SavedExercisesPage` y los campos `page`/`page_size` en `ListSavedExercisesFilters` en `frontend/src/app/core/generations-api.model.ts`; verificar que compila con `npm run build`.
- [x] 2.2 Cambiar `listSaved` en `generations-api.service.ts` para enviar `page`/`page_size` como `HttpParams` y devolver `Observable<SavedExercisesPage>`, actualizando `generations-api.service.spec.ts` para comprobar los parametros y la forma del sobre; verificar con `npm test`.

## 3. Componente de paginacion (Tailwind UI "Pagination")

- [x] 3.1 Crear el componente standalone reutilizable de paginacion en `frontend/src/app/core/` (patron numerado Anterior/Siguiente de Tailwind UI) con `input` de pagina actual y total de paginas, `output` `pageChange`, numeros de pagina, extremos deshabilitados y `focus-ring`; verificar con un test que en pagina 1 deshabilita Anterior, en la ultima deshabilita Siguiente y que pulsar un numero emite `pageChange`.
- [x] 3.2 Verificar que el componente respeta el lenguaje visual del tema (superficie, `border`, `text-content`/`text-muted`, estado deshabilitado) revisando contraste y foco con teclado en el test de render.

## 4. Pantalla `/ejercicios` y edicion de bloques

- [x] 4.1 Adaptar `tech-lead/bloque-editar/bloque-editar.ts` a la nueva forma de respuesta leyendo `items` (sin pasar paginacion) y actualizar su test; verificar con `npm test` que sigue mostrando todo el catalogo filtrado.
- [x] 4.2 Anadir a `EjerciciosComponent` los signals `page`, `total` y la constante `pageSize = 10`, `totalPages` calculado, y pasar `page`/`page_size` en `loadSaved()`; verificar con un test que la primera carga pide `page: 1, page_size: 10`.
- [x] 4.3 Resetear `page` a 1 en `onFilterTypeChange` y `onSearchTextChange`, y anadir `onPageChange(pagina)` que fije `page` y recargue; verificar con tests que cambiar filtro/busqueda llama a `listSaved` con `page: 1` y que `onPageChange` pide la pagina indicada.
- [x] 4.4 Hacer que `eliminar()` retroceda a la pagina anterior (o la primera) cuando la pagina actual queda vacia, y anadir los tests correspondientes; verificar con `npm test`.
- [x] 4.5 Mostrar el componente de paginacion en `ejercicios.html` debajo de la tabla solo cuando `totalPages > 1`, conectado a `onPageChange`; verificar con un test que con 11 coincidencias aparece el control y con 10 o menos no.
- [x] 4.6 Mantener la tabla montada (atenuada) al recargar por cambio de pagina/filtro, con el placeholder "Cargando…" solo en la primera carga, para que la pagina no encoja y el scroll no salte hacia arriba; verificar con un test que tras `onPageChange` la tabla sigue renderizada y no aparece "Cargando…".

## 5. Verificacion de integracion

- [x] 5.1 Ejecutar `npm test` y `npm run build` en `frontend/` y confirmar que pasan; ejecutar `openspec validate --change paginacion-ejercicios-guardados --strict` y confirmar que el cambio es coherente.
- [ ] 5.2 Con la app levantada, comprobar de punta a punta que `/ejercicios` muestra 10 por pagina, que el control navega, que filtro/busqueda vuelven a la pagina 1, y que `bloque-editar` sigue mostrando el catalogo completo.