# Tasks

## 1. Busqueda manual en el selector de ejercicios

- [x] 1.1 En `bloque-editar.ts`, sustituir el enlace directo del input por un `searchDraft` local (signal) que no dispare `cargarCatalogo()`; `onSearchTextChange`/el metodo equivalente solo actualiza el borrador y verificar que escribir en el campo no genera peticiones (inspeccionar las llamadas a `GenerationsApiService.listSaved` en los tests)
- [x] 1.2 Anadir un metodo `buscar()` (o similar) que copie `searchDraft` a `searchText` y llame a `cargarCatalogo()`, y enlazarlo al boton "Buscar" y al evento `keydown.enter` del input en `bloque-editar.html`; verificar con un test que pulsar el boton o Enter con texto en el borrador lanza exactamente una llamada a `listSaved` con ese texto
- [x] 1.3 Verificar que el filtro de tipo (`onFilterTypeChange`) sigue recargando el listado inmediatamente al cambiarlo, sin tocar su comportamiento actual (test de regresion si no existe ya)
- [x] 1.4 Verificar que cambiar el borrador sin confirmar y luego cambiar el filtro de tipo no incluye el borrador sin confirmar en la peticion (usa el ultimo `searchText` confirmado, no el borrador)
- [x] 1.5 Actualizar/anadir tests en `bloque-editar.spec.ts` para los escenarios del spec delta (escribir sin confirmar, confirmar con boton, confirmar con Enter, cambio de tipo automatico) y ejecutar la suite de ese fichero para verificar que pasan
