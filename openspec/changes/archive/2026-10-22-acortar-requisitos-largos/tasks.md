# Tasks

## 1. Verificar los deltas

- [x] 1.1 Comprobar que la descripción de cada requisito modificado (texto hasta el primer `#### Scenario:`) mide 500 caracteres o menos, y que `exercise-catalog` conserva sus 12 escenarios, `frontend-security-headers` sus 3 y `technology-validation` sus 3
- [x] 1.2 Ejecutar `openspec validate acortar-requisitos-largos --strict` y verificar que termina sin errores

## 2. Archivar y sincronizar las specs

- [x] 2.1 Archivar el change (`/opsx:archive`) sincronizando los deltas, y verificar con `openspec validate --specs` que las 26 specs pasan y ya no aparece el aviso "Requirement text is very long" en `exercise-catalog`, `frontend-security-headers` ni `technology-validation`
- [x] 2.2 Comprobar con `git diff` que el único cambio en `openspec/specs/` son esos tres requisitos y que ningún escenario existente ha desaparecido

## 3. Documentación

- [x] 3.1 Actualizar `capstone/juniortrainer-capstone.md`: añadir el change al Anexo C.2 y corregir el recuento de cambios archivados (cabecera y resumen), verificando que la cifra coincide con `ls openspec/changes/archive` y que ambos apartados dan el mismo número
