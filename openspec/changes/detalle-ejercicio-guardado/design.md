# Design

## Context

La pantalla `/ejercicios` (`frontend/src/app/tech-lead/ejercicios/`) es un componente Angular 22 standalone que pinta la tabla de "Guardados" a partir de `SavedExerciseListItem`, que ya incluye `name`, `type`, `statement`, `code` (`ExerciseCodeBlock[]`), `expected_answer`, `technologies`, `repo` y `block_usage_count` (ver `core/generations-api.model.ts`). Por tanto el detalle no necesita ninguna consulta nueva.

El proyecto no usa libreria de componentes: los controles se escriben a mano con Tailwind v4 y tokens del tema oscuro (`focus-ring`, `btn`, `input`, `card`, colores `surface`/`border`/`muted`/`content`). Ya existe un dialogo modal propio (`core/confirm-dialog.ts` + `.html`) montado una vez en `app.html`, con overlay `fixed inset-0 z-50 bg-black/70` y cierre con Escape.

Ver proposal.md - Why para la motivacion.

## Goals / Non-Goals

**Goals:**

- Ver el contenido completo de un ejercicio guardado desde el propio listado, sin salir de `/ejercicios` ni navegar a otra ruta.
- Reutilizar los datos ya cargados en el item del listado (sin endpoint nuevo).
- Mantener el lenguaje visual del tema oscuro y el patron de overlay ya existente.

**Non-Goals:**

- Editar el ejercicio desde el detalle (sigue siendo inmutable; la edicion no forma parte del catalogo).
- Mostrar el detalle desde otras pantallas (por ejemplo, la composicion de bloques).
- Anadir buscador, descarga o copia del contenido.
- Cambios de backend, contrato de API o base de datos.

## Decisions

**D1 - Modal centrado con cuerpo desplazable, no drawer.**
Se elige un modal (overlay a pantalla completa + tarjeta centrada) en lugar de un drawer lateral, por coherencia con el unico patron de overlay ya establecido en la app (`confirm-dialog`). El cuerpo de la tarjeta se limita en altura (`max-h`) y se desplaza (`overflow-y-auto`) para acomodar enunciados y bloques de codigo largos. Alternativa descartada: drawer lateral, que introduciria un segundo lenguaje visual para el mismo tipo de interaccion sin un beneficio claro aqui.

**D2 - Componente presentacional reutilizable en `core/`.**
Se crea `ExerciseDetailComponent` standalone en `frontend/src/app/core/` (junto a `confirm-dialog` y `pagination`): recibe el ejercicio a mostrar como `input` (`SavedExerciseListItem | null`) y emite un evento al cerrarse. No conoce `GenerationsApiService` ni el estado de la pantalla; solo pinta. Alternativa descartada: incrustar el modal directamente en `ejercicios.html`, que mezclaria la responsabilidad de presentacion con la de la pantalla y dificultaria los tests aislados.

**D3 - Estado de seleccion en `EjerciciosComponent`.**
`EjerciciosComponent` anade una signal `selected` (`SavedExerciseListItem | null`). El boton "Ver" de cada fila la fija con el item correspondiente; el evento de cierre del panel la vuelve a `null`. Todo el detalle sale del item ya en memoria, asi que no hay carga asincrona ni estado de error nuevo. El modal solo se monta cuando `selected()` no es `null` (`@if`), igual que `confirm-dialog`.

**D4 - Boton "Ver" en la columna de acciones, junto a "Eliminar".**
La ultima columna de la tabla pasa a tener "Ver" (accion no destructiva) y "Eliminar". "Ver" se estiliza como accion neutra (mismo tratamiento que el resto de acciones no destructivas del tema) para no competir visualmente con el rojo de "Eliminar".

**D5 - Cierre por boton, Escape y fondo.**
Siguiendo `confirm-dialog` y el requisito de accesibilidad ya usado, el panel se cierra con un boton "Cerrar", con la tecla Escape y con clic en el overlay. El foco inicial recae en el boton de cierre. Se marca como `role="dialog"` con `aria-modal="true"` y una etiqueta accesible con el nombre del ejercicio.

## Risks / Trade-offs

- [Contenido muy largo (enunciado + varios bloques de codigo) en un modal centrado] -> El cuerpo se limita en altura y se desplaza; la cabecera con el nombre y el boton de cierre quedan fijos.
- [Duplicar logica de overlay respecto a `confirm-dialog`] -> Aceptado: son responsabilidades distintas (confirmacion vs visualizacion); ambos componentes son pequenos y puramente presentacionales. No se justifica abstraer un overlay generico.
- [El detalle depende de que el item del listado traiga todos los campos] -> Ya los trae hoy (`SavedExerciseListItem` extiende `ExerciseCandidate`); si en el futuro el listado se aligerase, habria que anadir una consulta de detalle (fuera de alcance).

## Migration Plan

- Sin migraciones de base de datos ni cambios de backend.
- Despliegue: solo frontend; no requiere coordinacion con el backend.
- Rollback: revertir el cambio de frontend (sin estado persistido que migrar).

## Open Questions

- Ninguna que cambie el alcance, los specs o el desglose de tareas. La eleccion modal (frente a drawer) y el componente reutilizable quedan fijados en este diseno.