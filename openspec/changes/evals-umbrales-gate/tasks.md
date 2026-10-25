# Tasks

## 1. Tabla de umbrales

- [ ] 1.1 Crear `evals/thresholds.json` con los umbrales de la línea base de §5.7 (por agente y métrica; `agent: "*"` para los comunes como los falsos positivos de guardarraíl) y verificar que carga
- [ ] 1.2 Documentar en `evals/README.md` el formato de la tabla y que los umbrales son un dato editable que fija quien opera

## 2. Módulo del gate

- [ ] 2.1 Crear `evals/gates.py` (función pura): dado un informe y la tabla, devolver la lista de métricas que incumplen (agente, métrica, valor, umbral) y las que quedaron sin evaluar; verificar con tests de valores calculados a mano
- [ ] 2.2 Integrar `--gates` en `evals/run.py`: aplica el gate solo en modo real, imprime los incumplimientos y termina con código distinto de cero si los hay; rechaza `--gates` fuera de real. Verificar que sin incumplimientos sale 0 y con uno sale distinto de cero nombrando la métrica

## 3. Integración continua y documentación

- [ ] 3.1 Añadir a `.github/workflows/ci.yml` el job `evals-gate` con `workflow_dispatch`, que corre `python -m evals.run --mode real --gates` contra el entorno `develop` con la URL y las claves por secretos; documentar que el entorno y sus secretos son infraestructura
- [ ] 3.2 Documentar el gate en `evals/README.md` (cómo se ejecuta, qué hace y que no corre en cada PR)

## 4. Integración

- [ ] 4.1 Ejecutar `python -m unittest discover -s evals -t . -p "test_*.py"` y verificar que todo pasa sin red
- [ ] 4.2 Actualizar §5.3 del capstone (el gate ya existe; el resto del CI/CD sigue pendiente) — rama aparte