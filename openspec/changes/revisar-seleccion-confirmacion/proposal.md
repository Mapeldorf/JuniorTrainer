# Proposal

## Why

En "Revisar generacion" (`/ejercicios/:generationId/revisar`) el tech lead marca uno a uno los candidatos que quiere guardar antes de pulsar "Guardar ejercicios"; el resto se descarta para siempre (el requisito "Cierre de la revision de una generacion" ya especifica que cerrar la revision pasa la generacion a `done` y los candidatos sin marcar quedan sin guardar, sin vuelta atras). Hoy esa pantalla arranca con todos los candidatos SIN marcar (`selected.set({})` en `revisar.ts`), no hay forma de marcarlos o desmarcarlos todos de golpe, y el boton "Guardar ejercicios" ejecuta el guardado y el cierre inmediatamente, sin ningun aviso de que lo no marcado se pierde. El flujo normal (guardar casi todos los candidatos de una generacion) obliga a marcar uno a uno, y un clic en el boton puede descartar candidatos sin que el tech lead se de cuenta de que eso es irreversible.

## What Changes

- Al cargar la generacion, todos los candidatos aparecen marcados por defecto (en vez de ninguno).
- Se anade un control para marcar/desmarcar todos los candidatos de golpe.
- Al pulsar "Guardar ejercicios", si queda algun candidato sin marcar, se muestra un aviso que dice que esos candidatos se van a perder para siempre y da a elegir entre continuar (guarda los marcados y cierra la generacion, como hasta ahora) o cancelar (vuelve a la pantalla de revision sin cambiar nada). Si todos los candidatos ya estan marcados, no hay nada que perder y el guardado procede sin aviso.
- No se toca el backend ni el contrato de ningun endpoint: el comportamiento ya especificado (los candidatos sin marcar se descartan al cerrar la revision) no cambia, solo como el frontend guia al tech lead hacia esa decision. Por eso este change declara `skip_specs: true` (ver `.openspec.yaml`): no hay ningun requisito de `openspec/specs/` que anadir o modificar.
- Fuera de alcance: no se cambia que pasa con los candidatos sin marcar (se siguen descartando igual), ni se anade una confirmacion al boton "Cancelar" (ese ya es explicitamente un abandono sin guardar nada, sin ambiguedad que avisar).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna (`skip_specs: true`): el comportamiento observable a nivel de API no cambia; ver Why/What Changes.

## Impact

- `frontend/src/app/tech-lead/revisar/revisar.ts`: `cargarDetalle()` inicializa `selected` con todos los candidatos a `true`; nuevo metodo para marcar/desmarcar todos; `guardar()` comprueba si hay candidatos sin marcar antes de proceder y, si los hay, pide confirmacion primero.
- `frontend/src/app/tech-lead/revisar/revisar.html`: nuevo control de "marcar/desmarcar todos" junto a la lista de candidatos; el dialogo de confirmacion (componente a decidir en design.md).
- `frontend/src/app/tech-lead/revisar/revisar.spec.ts`: nuevos casos para la preseleccion, el marcar/desmarcar todos, y el flujo de confirmacion (continuar guarda y cierra; cancelar no cambia nada).
- Sin cambios en `backend/`, en ningun schema, ni en `openspec/specs/`.
