# Proposal

## Why

En el formulario de bloque de ejercicios (`/bloques/nuevo` y `/bloques/:blockId/editar`), el campo de busqueda del selector de ejercicios lanza una peticion `GET /exercises` al backend en cada caracter que el tech lead escribe (`onSearchTextChange` se dispara en cada `ngModelChange`). Esto genera trafico innecesario y, con conexiones lentas, respuestas que llegan desordenadas mientras el usuario sigue escribiendo. La busqueda debe lanzarse solo cuando el tech lead decide ejecutarla.

## What Changes

- El campo de texto del selector de ejercicios deja de disparar la busqueda en cada pulsacion; el texto escrito se mantiene en un borrador local que no afecta al listado hasta confirmarse.
- Se anade una accion explicita para ejecutar la busqueda por texto (boton "Buscar"), y pulsar Enter en el campo tiene el mismo efecto.
- El filtro por tipo (`select`) no cambia: sigue recargando el listado automaticamente al seleccionarlo.
- Si el tech lead cambia el texto y navega fuera sin confirmar, el listado sigue reflejando la ultima busqueda confirmada, no el borrador.

## Capabilities

### Modified Capabilities
- `exercise-blocks`: el requisito del selector de ejercicios del formulario de bloque pasa a buscar por texto solo cuando el tech lead lo confirma (boton o Enter), no en cada caracter.

## Impact

- `frontend/src/app/tech-lead/bloque-editar/bloque-editar.ts`: separar el texto del input (borrador) del texto de busqueda confirmado; `onSearchTextChange` deja de llamar a `cargarCatalogo()` en cada cambio; se anade un metodo para confirmar la busqueda.
- `frontend/src/app/tech-lead/bloque-editar/bloque-editar.html`: el input de busqueda se enlaza al borrador; se anade un boton "Buscar" junto al input y un manejador de Enter.
- No afecta al backend (`GET /exercises` no cambia) ni a la pantalla de "ejercicios guardados" (`exercise-catalog`), que ya tiene su propio flujo de filtros.
