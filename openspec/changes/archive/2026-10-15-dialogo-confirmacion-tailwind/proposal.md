# Proposal

## Why

Las tres confirmaciones destructivas de la aplicación (eliminar un ejercicio guardado, eliminar un bloque, guardar una revisión con candidatos sin marcar) usan `window.confirm()`, un diálogo nativo del navegador/Windows que rompe el estilo visual de la app y no se puede personalizar (texto de botones fijo del sistema operativo, sin la paleta zinc/blue ni los componentes ya establecidos).

## What Changes

- **BREAKING**: `window.confirm()` deja de usarse en toda la aplicación.
- Nuevo componente de diálogo de confirmación modal, con Tailwind, reutilizable: panel centrado con overlay, título, mensaje, y dos botones configurables (texto de confirmar/cancelar, y si la acción es destructiva, para colorear el botón de confirmar en rojo).
- Nuevo servicio compartido que abre el diálogo y devuelve el resultado de forma asíncrona (un diálogo en pantalla no puede bloquear de forma síncrona como `window.confirm()`).
- Los tres puntos de uso existentes (`EjerciciosComponent.confirmarEliminar`, `BloqueDetalleComponent.confirmarEliminar`, `RevisarComponent.confirmarPerdida`) pasan de devolver un `boolean` síncrono a devolver una promesa/observable, y sus llamadores (`eliminar()`, `eliminar()`, `guardar()`) pasan a esperar ese resultado antes de continuar.
- Soporte de teclado: `Escape` cancela, el foco inicial cae en un botón razonable (cancelar, para no facilitar una confirmación destructiva accidental al pulsar Enter).

## Capabilities

### New Capabilities
- `confirm-dialog`: cómo el sistema presenta una confirmación que requiere una decisión explícita del usuario (confirmar o cancelar) antes de continuar con una acción, de forma asíncrona y con apariencia propia de la aplicación.

### Modified Capabilities
Ninguna. `exercise-catalog` (borrar un ejercicio guardado), `exercise-blocks` (borrar un bloque) y `exercise-generation`/`revisar-seleccion-confirmacion` (confirmar pérdida de candidatos sin marcar) no cambian su comportamiento observable a nivel de negocio — siguen pidiendo confirmación antes de la misma acción destructiva; solo cambia el mecanismo de UI con el que se pide esa confirmación.

## Impact

- **Nuevo** `frontend/src/app/core/confirm-dialog.service.ts` (o ubicación equivalente): servicio inyectable que abre el diálogo y devuelve el resultado.
- **Nuevo** componente del diálogo (standalone, Tailwind), montado una vez a nivel de aplicación (p. ej. en `app.html`/`app.ts`) para que cualquier componente pueda pedir una confirmación sin montar nada por su cuenta.
- **Modificados**: `frontend/src/app/tech-lead/ejercicios/ejercicios.ts` (+ `.spec.ts`), `frontend/src/app/tech-lead/bloque-detalle/bloque-detalle.ts` (+ `.spec.ts`), `frontend/src/app/tech-lead/revisar/revisar.ts` (+ `.spec.ts`): sus métodos de confirmación pasan a ser asíncronos.
- Sin cambios en backend ni en especificación de negocio.
