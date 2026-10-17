# Proposal

## Why

En la pantalla `/ejercicios`, la tabla de "Guardados" solo muestra un resumen (nombre, tipo, tecnologias y repositorio) y no hay forma de consultar el enunciado, el codigo ni la respuesta esperada de un ejercicio ya guardado sin abrir la edicion de bloques. El tech lead necesita poder inspeccionar el contenido completo de un ejercicio desde el propio listado.

## What Changes

- Anadir un boton "Ver" en cada fila de la tabla de "Guardados" de `/ejercicios`.
- Al pulsarlo, abrir un panel de detalle (modal/drawer Tailwind propio) con la informacion completa del ejercicio: nombre, tipo, tecnologias, repositorio, enunciado, bloques de codigo y respuesta esperada.
- El panel es de solo lectura y no requiere ninguna llamada nueva al backend: reutiliza los datos ya presentes en el item del listado (`SavedExerciseListItem`).
- Cerrar el panel con un boton, con Escape y/o clic en el fondo.

## Capabilities

### New Capabilities
- (ninguna)

### Modified Capabilities
- `exercise-catalog`: se anade el requisito de consultar en la interfaz el detalle completo de un ejercicio guardado desde el listado.

## Impact

- Frontend: `frontend/src/app/tech-lead/ejercicios/` (componente, plantilla y tests) y un componente de detalle reutilizable nuevo en `frontend/src/app/core/`.
- Sin cambios de backend, de contrato de API ni de base de datos.