# Tasks

## 1. Servicio y componente del diálogo

- [x] 1.1 Crear `frontend/src/app/core/confirm-dialog.model.ts` con el tipo de la petición (`title`, `message`, `confirmLabel`, `cancelLabel`, `destructive?: boolean`). Verificar con `npx tsc --noEmit` sin errores.
- [x] 1.2 Crear `frontend/src/app/core/confirm-dialog.service.ts` (`ConfirmDialogService`, `providedIn: 'root'`): signal `request: Signal<ConfirmDialogRequest | null>`, método `confirm(options): Promise<boolean>` que fija el signal y una promesa pendiente, y métodos internos `resolveConfirm()`/`resolveCancel()` que resuelven la promesa y vacían el signal. Si `confirm()` se llama con una petición ya activa, la anterior se resuelve como `false` antes de mostrar la nueva (design.md - Decisions). Verificar con un test unitario del servicio: `confirm()` devuelve una promesa que resuelve `true`/`false` según se llame a `resolveConfirm`/`resolveCancel`; una segunda llamada a `confirm()` con una petición activa resuelve la primera como `false`.
- [x] 1.3 Crear el componente standalone `frontend/src/app/core/confirm-dialog.ts` + `confirm-dialog.html`: lee `request()` del servicio, no renderiza nada si es `null`; si no, overlay `fixed inset-0 bg-black/50` + panel `rounded-xl border border-zinc-200 bg-white p-6` con título, mensaje, botón de confirmar (rojo si `destructive`, azul si no) y botón de cancelar, con las clases ya usadas en el resto de la app (design.md - Decisions, estilo visual). Verificar con un test de componente: con una petición activa, se renderizan el título/mensaje/textos de botón indicados; pulsar cada botón llama al método correspondiente del servicio.
- [x] 1.4 Añadir a ese componente: foco inicial en el botón de cancelar al abrirse (requisito "Cierre con teclado"), y `(keydown.escape)` en el contenedor raíz que cancela igual que el botón. Verificar con un test de componente: al emitir una petición, el botón de cancelar queda enfocado; un evento `keydown.escape` sobre el diálogo resuelve como cancelado.

## 2. Montaje global

- [x] 2.1 Montar `<app-confirm-dialog />` una vez en `app.html`, junto al `<router-outlet>`. Verificar que `app.spec.ts` sigue en verde y que el componente aparece en el DOM del `AppComponent` (oculto, sin petición activa).

## 3. Migrar los tres puntos de uso

- [x] 3.1 En `frontend/src/app/tech-lead/ejercicios/ejercicios.ts`: `confirmarEliminar(exercise)` pasa a usar `ConfirmDialogService.confirm(...)` y a devolver `Promise<boolean>`; `eliminar(exercise)` pasa a `async` y espera el resultado antes de borrar (mismo texto ya usado: "¿Eliminar el ejercicio "<nombre>"?"). Actualizar `ejercicios.spec.ts` (mock de `ConfirmDialogService`, `await` en las llamadas a `eliminar()`). Verificar con `ng test` sobre ese componente.
- [x] 3.2 Mismo cambio en `frontend/src/app/tech-lead/bloque-detalle/bloque-detalle.ts` (`confirmarEliminar()`/`eliminar()`, texto "¿Eliminar el bloque "<nombre>"?") y su `.spec.ts`. Verificar con `ng test` sobre ese componente.
- [x] 3.3 Mismo cambio en `frontend/src/app/tech-lead/revisar/revisar.ts` (`confirmarPerdida(count)`/`guardar()`, mismo texto ya usado sobre candidatos sin marcar) y su `.spec.ts`. Verificar con `ng test` sobre ese componente.
- [x] 3.4 Confirmar que no queda ninguna llamada a `confirm(`/`alert(` nativos en `frontend/src/` (búsqueda en el código). Verificar que la suite completa de frontend (`ng test --watch=false`) sigue en verde.

## 4. Verificación visual

- [x] 4.1 Levantar el frontend en el navegador y comprobar a ojo las tres confirmaciones (eliminar ejercicio, eliminar bloque, guardar revisión con candidatos sin marcar): aparecen con el estilo de la app (no un diálogo nativo), Escape cancela, y el foco inicial está en "Cancelar".
