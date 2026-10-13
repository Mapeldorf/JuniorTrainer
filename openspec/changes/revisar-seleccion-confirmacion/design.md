# Design

## Context

Ver proposal.md ("Why") para la motivacion. Estado actual relevante de `frontend/src/app/tech-lead/revisar/`:

- `revisar.ts` mantiene la seleccion en una signal `selected: Record<string, boolean>` (mapa candidato->marcado), consultada con `isSelected(id)` y cambiada con `toggleSelected(id)`. `cargarDetalle()` la resetea a `{}` (nada marcado) cada vez que carga una generacion.
- `guardar()` filtra `candidates` por `isSelected`, guarda cada uno marcado (con su nombre/respuesta esperada editados si cambiaron, change `ejercicios-con-nombre`) y, en cualquier caso (incluso 0 marcados), cierra la generacion con `api.close()` y navega a `/ejercicios`. No hay ningun paso intermedio hoy.
- El proyecto no tiene Angular Material/CDK instalado (`frontend/package.json`); las dos confirmaciones destructivas que ya existen (`bloque-detalle.ts` al eliminar un bloque, `ejercicios.ts` al eliminar un ejercicio guardado) usan el `confirm()` nativo del navegador, envuelto en un metodo propio del componente (`confirmarEliminar()`) para poder sustituirlo (`vi.spyOn`) en los tests sin depender de un dialogo real.
- No hay ningun componente de modal/dialogo propio en el proyecto todavia.

## Goals / Non-Goals

**Goals:**

- Que el camino mas comun (guardar casi todos los candidatos) no exija marcarlos uno a uno.
- Que marcar/desmarcar todos sea una sola accion.
- Que perder candidatos sin querer sea dificil: un aviso explicito antes de confirmar la perdida, en vez de una perdida silenciosa.
- Mantener el mismo patron de confirmacion que ya usa el resto de la aplicacion (consistencia, sin anadir dependencias).

**Non-Goals:**

- No se construye un componente de modal/dialogo reutilizable: una sola pantalla lo necesita hoy, y el patron ya establecido (`confirm()` nativo envuelto) resuelve el caso sin esa inversion.
- No se cambia la logica de guardado/cierre en si (`guardar()` sigue guardando los marcados y cerrando la generacion); solo se le antepone una comprobacion.
- No se persiste la preferencia de seleccion entre visitas: cada carga de la pantalla vuelve a preseleccionar todo.

## Decisions

### 1. Preseleccion: `cargarDetalle()` inicializa `selected` con todos a `true`

En vez de `this.selected.set({})`, se construye el mapa igual que ya se hace con `editedAnswers`/`editedNames` (un `for` sobre `detail.candidates`), poniendo cada id a `true`. Minimiza el diff y seguida exactamente el patron que el propio fichero ya usa para los otros dos mapas por candidato.

### 2. Marcar/desmarcar todos: un unico checkbox con un computed `allSelected()`

Se anade una signal computada `allSelected = computed(() => { const c = this.detail()?.candidates ?? []; return c.length > 0 && c.every((x) => this.isSelected(x.id)); })` y un metodo `toggleAll()` que, si `allSelected()` es true, desmarca todos; si no, marca todos. En la plantilla, un checkbox encima de la lista de candidatos, con `[checked]="allSelected()"` y `(change)="toggleAll()"`, con la etiqueta "Seleccionar todos".

Alternativa descartada: dos botones separados ("Seleccionar todos" / "Deseleccionar todos"). Un unico checkbox con estado reflejado (marcado solo cuando TODOS lo estan) es el patron estandar para esta accion, ocupa menos espacio, y no necesita logica adicional para decidir cual de los dos botones mostrar activo.

Alternativa descartada: estado "indeterminado" visual cuando hay una seleccion parcial (la propiedad `indeterminate` de un checkbox no es un atributo HTML, hay que fijarla por JS sobre el elemento nativo). Anade complejidad (una referencia de plantilla + un efecto) para una senal puramente cosmetica que no cambia ningun comportamiento; se deja fuera.

### 3. Confirmacion de perdida: mismo patron que `confirmarEliminar()`, con `confirm()` nativo

`guardar()` calcula `marked` como ya hace; si `marked.length < candidates.length` (hay al menos un candidato sin marcar), llama a un nuevo metodo `confirmarPerdida(candidates.length - marked.length): boolean` que envuelve `confirm()` con un mensaje que nombra cuantos candidatos se van a perder, antes de continuar con el guardado+cierre ya existente. Si el tech lead cancela (`confirmarPerdida()` devuelve `false`), `guardar()` termina ahi sin tocar `saving`/`error` ni llamar a la API: la pantalla se queda exactamente como estaba, con la seleccion intacta, para poder seguir editando (requisito "cancelar para seguir editando").

Si `marked.length === candidates.length` (todo marcado, preseleccion sin tocar), no hay nada que perder: se omite la confirmacion y se guarda directamente, igual que hoy.

Alternativa descartada: un componente de modal propio (HTML/CSS a medida) para el aviso. Se descarta por las razones del Non-Goal: una sola pantalla lo necesita, el patron ya existente (`confirm()` envuelto, probado dos veces en el proyecto) resuelve exactamente el mismo problema (accion irreversible, pedir confirmacion, ser sustituible en tests), y no hay ninguna necesidad de estilos propios o de contenido enriquecido en el aviso (es una frase).

Alternativa descartada: deshabilitar el boton "Guardar ejercicios" hasta que no haya nada sin marcar. Contradice el requisito explicito: el tech lead SHALL poder guardar solo una parte y descartar el resto a proposito (es el flujo normal de revision, ya cubierto por el requisito "Cerrar la revision con candidatos sin guardar"); forzar a marcar todo para poder guardar romperia ese flujo.

## Risks / Trade-offs

- **`confirm()` nativo no es visualmente vistoso ni personalizable** (texto plano, sin la lista de nombres de los candidatos que se pierden) → aceptado por consistencia con el resto de la app; el mensaje si incluye el numero de candidatos que se van a perder, que es la informacion que importa para decidir.
- **Un tech lead que SIEMPRE deja algo sin marcar vera el aviso en cada generacion** → es el comportamiento pedido explicitamente (avisar siempre que se vaya a perder algo); no se anade una opcion de "no volver a preguntar" porque no se pidio y anadiria estado a persistir sin necesidad clara.
- **Cambiar el default de "nada marcado" a "todo marcado" puede sorprender a quien ya conocia el comportamiento anterior** → mitigado por el propio aviso de la decision 3: si alguien desmarca candidatos a proposito y pulsa guardar, el aviso se lo confirma antes de perderlos.

## Migration Plan

Sin migracion de datos ni de API: solo codigo de frontend (`revisar.ts`/`revisar.html`/`revisar.spec.ts`). Desplegar es reconstruir la imagen del frontend. El rollback es revertir el commit: no hay estado persistido que deshacer.
