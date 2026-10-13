# Tasks

## 1. Preseleccion de todos los candidatos

- [ ] 1.1 En `frontend/src/app/tech-lead/revisar/revisar.ts`, cambiar `cargarDetalle()` para que `selected` se inicialice con todos los `detail.candidates` a `true` (en vez de `this.selected.set({})`), mismo patron `for` que ya usa para `editedAnswers`/`editedNames`. Verificar con `npx ng test`: ampliar el test "generacion lista (ready): muestra los candidatos..." (o anadir uno nuevo) para comprobar que, tras cargar, `component.isSelected('c1')` e `isSelected('c2')` son `true` sin haber hecho ningun click.

## 2. Marcar/desmarcar todos de golpe

- [ ] 2.1 Anadir en `revisar.ts` la signal computada `allSelected` (true solo si hay candidatos y todos estan marcados, design.md decision 2) y el metodo `toggleAll()` (si `allSelected()` es true desmarca todos, si no los marca todos). Verificar con `npx ng test`: con los dos candidatos marcados, `allSelected()` es `true`; tras `toggleSelected('c1')`, `allSelected()` pasa a `false`; `toggleAll()` sobre una seleccion parcial marca los dos; `toggleAll()` sobre todo marcado los desmarca todos.
- [ ] 2.2 Anadir en `revisar.html` un checkbox "Seleccionar todos" encima de la lista de candidatos, con `[checked]="allSelected()"` y `(change)="toggleAll()"`. Verificar con `npx ng test`: tras `fixture.detectChanges()`, el checkbox con esa etiqueta existe y su estado `checked` refleja `allSelected()` (marcado al cargar, por la preseleccion de la tarea 1.1).

## 3. Confirmacion antes de perder candidatos sin marcar

- [ ] 3.1 Anadir en `revisar.ts` el metodo `confirmarPerdida(count: number): boolean` que envuelve `confirm()` (mismo patron que `confirmarEliminar()` en `ejercicios.ts`/`bloque-detalle.ts`), con un mensaje que nombra cuantos candidatos se van a perder. Verificar con `npx ng test`: `vi.spyOn(window, 'confirm')` devuelve lo que `confirm()` devolvio, y el mensaje pasado a `confirm()` contiene el numero de candidatos.
- [ ] 3.2 Modificar `guardar()` para que, si `marked.length < candidates.length`, llame a `confirmarPerdida(candidates.length - marked.length)` antes de proceder; si devuelve `false`, `guardar()` termina sin cambiar `saving()`/`error()` ni llamar a `api.save()`/`api.close()` (design.md decision 3); si devuelve `true`, o si no hay nada sin marcar, continua exactamente igual que antes. Verificar con `npx ng test`: (a) con una seleccion parcial y `confirmarPerdida` mockeado a `false`, `guardar()` no llama a `save` ni a `close`, y `saving()` sigue en `false`; (b) con una seleccion parcial y `confirmarPerdida` mockeado a `true`, `guardar()` guarda y cierra como antes; (c) con todo marcado (el default tras la tarea 1.1), `guardar()` guarda y cierra sin llamar a `confirmarPerdida` en absoluto.

## 4. Verificacion manual (a cargo del usuario)

- [ ] 4.1 El usuario prueba en el navegador, con el stack levantado: revisar una generacion real y confirmar que todos los candidatos salen premarcados; desmarcar uno, usar "Seleccionar todos" para volver a marcarlo, y desmarcarlo con el mismo control para comprobar que alterna; desmarcar un candidato y pulsar "Guardar ejercicios", comprobando que aparece el aviso con el conteo correcto, que "Cancelar" (en el dialogo nativo) deja la pantalla intacta para seguir editando, y que confirmar guarda los marcados y cierra la generacion; repetir con todos marcados para comprobar que no aparece ningun aviso.
