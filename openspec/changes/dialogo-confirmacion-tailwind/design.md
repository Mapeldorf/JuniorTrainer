# Design

## Context

Ver `proposal.md` - Why. Los tres usos actuales de `confirm()` ya están aislados cada uno en su propio método del componente (`confirmarEliminar`/`confirmarPerdida`), pensados explícitamente para poder sustituirse sin tocar el resto del componente. El stack es Angular 22 standalone + signals, Tailwind v4 con clases utilitarias directas en las plantillas, sin Angular CDK ni ninguna librería de componentes UI.

## Goals / Non-Goals

**Goals:**
- Un servicio + componente reutilizable que sustituya los tres usos de `window.confirm()` sin añadir una dependencia nueva.
- Mantener el patrón ya establecido en el proyecto: standalone components, signals, sin NgRx ni librerías de overlay.

**Non-Goals:**
- Diálogos apilados/anidados: la aplicación nunca pide dos confirmaciones a la vez; el diseño no necesita soportarlo.
- Un sistema genérico de "modal" para cualquier contenido (formularios, imágenes, etc.) — solo confirmación de dos acciones (confirmar/cancelar) con título y mensaje de texto.
- Migrar los `role="alert"` de error ya existentes (inline, con señal `error()`): no son diálogos de confirmación y quedan fuera de este change.

## Decisions

**Un servicio (`ConfirmDialogService`) con un signal de "petición actual" (`request: Signal<ConfirmDialogRequest | null>`), más un componente (`ConfirmDialogComponent`) montado UNA VEZ en `app.html`, junto al `<router-outlet>`.** El servicio expone `confirm(options): Promise<boolean>`: fija el signal con la petición (título, mensaje, textos de los botones, si es destructiva) y una `resolve` pendiente; el componente, que lee ese mismo signal, se renderiza (o no) según si hay petición activa, y al pulsar un botón llama a un método del servicio que resuelve la promesa y vacía el signal. Alternativa descartada: crear el componente dinámicamente en cada punto de uso con `ViewContainerRef.createComponent()` — monta y destruye un componente en cada uno de los tres sitios, duplicando la gestión de ciclo de vida sin ninguna ventaja, cuando montarlo una vez a nivel de `app.html` ya cubre toda la aplicación.

**`confirm()` devuelve una `Promise<boolean>` (no un `Observable`).** Encaja con `async`/`await` en los tres llamadores (`eliminar()`, `guardar()`), que ya son métodos imperativos de un solo uso (no un stream continuo); no hay ninguna necesidad de cancelación ni de múltiples emisiones que justifique un `Observable`.

**Sin diálogos anidados: una segunda llamada a `confirm()` mientras ya hay uno abierto resuelve el anterior como `false` (cancelado) antes de mostrar el nuevo.** No es un caso real de la aplicación (ninguno de los tres puntos de uso puede disparar al mismo tiempo), pero deja un comportamiento definido en vez de un signal pisado sin resolver su promesa, que dejaría una `Promise` colgada para siempre.

**Teclado sin Angular CDK.** Sin `cdkTrapFocus` disponible, el foco inicial se fija a mano: un `viewChild` del botón de cancelar + `afterRenderEffect`/`effect` que llama a `.focus()` cuando la petición pasa de `null` a no-`null`. `Escape` se captura con `(keydown.escape)` en el contenedor raíz del propio diálogo (el elemento ya tiene el foco o un descendiente lo tiene, así que el evento burbujea hasta él). No se implementa un *focus trap* completo (ciclar Tab dentro del diálogo): con solo dos botones y un overlay que cubre el resto de la página, el riesgo de que Tab saque el foco del diálogo es bajo, y añadirlo a mano sin CDK es complejidad que ningún requisito pide.

**Migración de los tres puntos de uso: `boolean` síncrono → `Promise<boolean>`, y sus llamadores pasan a `async`.**
- `EjerciciosComponent.confirmarEliminar(exercise): Promise<boolean>`, llamado desde `eliminar()` (pasa a `async eliminar()`, con `if (!(await this.confirmarEliminar(exercise))) return;`).
- `BloqueDetalleComponent.confirmarEliminar(): Promise<boolean>`, mismo patrón en `eliminar()`.
- `RevisarComponent.confirmarPerdida(count): Promise<boolean>`, llamado desde `guardar()` (ya es un método que hace trabajo asíncrono después, solo cambia el `if` de la comprobación inicial).
- Los tests existentes que sustituyen estos métodos (`vi.fn().mockReturnValue(true/false)`) pasan a `mockResolvedValue(true/false)`, y los tests que los llaman directamente necesitan `await`.

**Estilo visual: reutiliza las clases ya establecidas, sin introducir una paleta nueva.** Overlay `fixed inset-0 bg-black/50`; panel `rounded-xl border border-zinc-200 bg-white p-6` (mismo radio/borde que las tarjetas de `revisar.html`/`ejercicios.html`); botón de confirmar destructivo con el mismo rojo que ya usa el botón "Eliminar bloque" (`border-red-300 text-red-700 hover:bg-red-50` para una acción secundaria visualmente, o `bg-red-700 text-white hover:bg-red-800` si se quiere más énfasis como acción primaria del diálogo — se decide en la tarea de implementación mirando cuál de las dos lee mejor como "acción principal destructiva" dentro de un diálogo, donde si tiene más peso visual que en una tabla); botón de cancelar igual que el "Cancelar" ya usado en `generar.html`/`revisar.html` (`rounded-lg border border-zinc-300 hover:bg-zinc-100`). Confirmar no-destructivo (si se necesitara en el futuro) usa el azul ya establecido (`bg-blue-700 hover:bg-blue-800`).

## Risks / Trade-offs

- [Convertir `eliminar()`/`guardar()` a `async` cambia su firma pública; cualquier test que llame a esos métodos sin `await` seguiría "pasando" pero sin esperar a que la promesa se resuelva, dando falsos positivos] → cubierto explícitamente en las tareas: cada test que invoque estos métodos pasa a `await`/`async`, verificado al migrar cada uno, no solo al final.
- [Sin *focus trap* completo, Tab puede sacar el foco del diálogo hacia elementos de detrás] → riesgo aceptado (Non-Goals); el overlay bloquea los clics sobre el fondo (`pointer-events` normales de un elemento por delante), así que como mucho se ve un foco visual fuera de sitio, no se puede interactuar con nada de detrás.
- [Un componente montado siempre en `app.html`, aunque esté oculto, añade un pequeño coste de change detection permanente] → coste despreciable (un signal check), mismo patrón que cualquier `@if` en Angular con signals.

## Migration Plan

Sin migración de datos (cambio puramente de frontend). Despliegue normal: se construye y se sirve la nueva versión del frontend: no hay API ni esquema que cambiar. Sin plan de rollback especial más allá de revertir el commit/PR si algo falla visualmente.
