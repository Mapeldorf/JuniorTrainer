# Tasks

## 1. Componente de detalle

- [x] 1.1 Crear `frontend/src/app/core/exercise-detail.ts` (componente standalone `ExerciseDetailComponent`) con un `input` de solo lectura `exercise: SavedExerciseListItem | null` y un `output` de cierre; `ng build` compila sin errores
- [x] 1.2 Crear `frontend/src/app/core/exercise-detail.html`: modal centrado con overlay `fixed inset-0 z-50 bg-black/70`, cabecera fija con nombre y botón "Cerrar", cuerpo desplazable (`max-h` + `overflow-y-auto`) con tipo, tecnologías, repositorio, enunciado, bloques de código y respuesta esperada (con texto alternativo cuando `expected_answer` es nulo), `role="dialog"` + `aria-modal="true"`; `ng build` compila sin errores
- [x] 1.3 Cerrar el panel con el botón, con Escape (`keydown.escape` en el overlay) y con clic en el fondo, con el foco inicial en el botón de cierre; verificado con tests
- [x] 1.4 Crear `frontend/src/app/core/exercise-detail.spec.ts` cubriendo: muestra todos los campos del ejercicio, indica ausencia de respuesta esperada, y emite el cierre por botón/Escape/fondo; `ng test` pasa

## 2. Integración en la pantalla de guardados

- [x] 2.1 Añadir el botón "Ver" en la columna de acciones de cada fila de la tabla de "Guardados" en `ejercicios.html`, junto a "Eliminar" y con estilo de acción neutra; `ng build` compila sin errores
- [x] 2.2 En `ejercicios.ts`, añadir la signal `selected` (`SavedExerciseListItem | null`), un método `ver(exercise)` que la fija y otro `cerrarDetalle()` que la limpia, e importar/montar `ExerciseDetailComponent` con `@if (selected())`; `ng build` compila sin errores
- [x] 2.3 Ampliar `ejercicios.spec.ts` para cubrir el requisito "Consultar el detalle de un ejercicio guardado": pulsar "Ver" abre el detalle con el item correcto y cerrar el panel vuelve al listado sin modificar el ejercicio; `ng test` pasa

## 3. Verificación

- [x] 3.1 Ejecutar `ng test` y `ng build` en `frontend/` y comprobar que todo pasa y compila
- [ ] 3.2 Comprobar manualmente en `/ejercicios` que "Ver" abre el detalle de cada ejercicio guardado y que se cierra con botón, Escape y clic en el fondo sin alterar el listado