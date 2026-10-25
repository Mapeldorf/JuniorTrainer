# Proposal

## Why

La suite de evaluación (§5.5) **mide** pero no **bloquea**: en modo real solo informa, aunque una métrica quede por debajo de lo deseable. El punto 4 de §5.3 pide un *gate* por umbral, y la línea base para fijarlos ya existe (§5.7: tres ejecuciones completas de los seis agentes). Sin umbrales, un cambio de prompt o de modelo degrada la calidad sin que nada lo impida.

## What Changes

- Una **tabla de umbrales versionada** (`evals/thresholds.json`) con los umbrales de las métricas de la suite, derivados de la línea base de §5.7.
- La suite **aplica los umbrales** en modo real con `--gates`: si una métrica baja del umbral, la ejecución termina con código distinto de cero y nombra la métrica incumplida. Una métrica sin casos se informa como no evaluada, no como fallo.
- Un job de CI **a demanda** (`evals-gate`, `workflow_dispatch`) que corre la suite real con `--gates` contra el entorno `develop`, con la URL y las claves por secretos. El entorno `develop` en vivo y sus secretos son infraestructura.
- Documentación en `evals/README.md`.

### Supuestos

- Los umbrales son una **decisión de quien opera** (como el tope de clave de §3.4): se fijan en el fichero y se ajustan ahí.
- El gate **no** corre en cada PR: necesita modelos reales y el stack; su sitio es `develop`, no el CI de PR.

### Fuera de alcance

- Construir el entorno `develop` (infraestructura) y sus secretos.
- Los umbrales de monitorización de producción (§5.8), que son otra cosa.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `agent-evaluation`: se añade el requisito de umbrales de calidad y gate.

## Impact

- Directorio `evals/` (tabla de umbrales, módulo del gate, `run.py`, README y tests); `.github/workflows/ci.yml` (job a demanda). Ningún cambio en el código de producción de los agentes.