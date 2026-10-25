# Design

## Context

Ver `proposal.md`. Lo comprobado:

- `evals/run.py` en modo real informa y sale con código 0 salvo error de ejecución (spec `agent-evaluation`, "El modo real no bloquea por umbral"). Este change añade el modo bloqueante, opcional.
- El informe por agente (`evals/report.py`) ya expone las métricas con rutas estables (`metrics.valid_output_rate`, `metrics.verdict.cohen_kappa`, `metrics.validator.gate.false_positive_rate`, `latency.p95_ms`…), que son las que el gate compara.
- La línea base de §5.7 (tres ejecuciones completas) da los valores de partida.

## Goals / Non-Goals

**Goals:**
- Convertir la línea base en umbrales y hacer que la suite pueda **fallar** por ellos, de forma explícita y legible.
- Que los umbrales sean **datos**, no código: se editan sin tocar el arnés.

**Non-Goals:**
- Correr el gate en cada PR (necesita modelos), ni construir el entorno `develop`.
- Umbrales del juez de contenido (§5.6) o de monitorización (§5.8).

## Decisions

**1. Umbrales en `evals/thresholds.json`, como lista.** Cada entrada lleva `agent` (o `*` para todos), `metric` (ruta en el informe), y un límite `min` o `max`. Es un dato editable: ajustar un umbral no toca código. *Alternativa descartada:* umbrales en el código; obligarían a un despliegue para cambiarlos.

**2. El gate es opcional y solo en modo real.** `--gates` activa la comprobación; sin el flag, la suite informa como hasta ahora. En modo simulado no tiene sentido (el doble guionizado no mide calidad), así que se rechaza, igual que `--reasoning`.

**3. Una métrica sin casos no es un fallo, es "no evaluada".** El informe ya trata `n/d` como ausencia de casos, no como cero; el gate lo respeta y lo informa aparte. *Trade-off:* un run que no ejercite una métrica podría pasar; se mitiga informando cuántas quedaron sin evaluar.

**4. El gate corre en `develop`, a demanda.** Como el modo real necesita LiteLLM y las claves de los agentes, el job es `workflow_dispatch` y toma la URL y las credenciales de secretos. Construir ese entorno y configurar sus secretos es infraestructura (§5.2), fuera de este change.

**5. Módulo puro y testeable.** `evals/gates.py` recibe un informe y la tabla y devuelve la lista de incumplimientos, sin E/S: se prueba con informes calculados a mano, como el resto de métricas.

## Risks / Trade-offs

- [Umbral mal puesto bloquea trabajo legítimo] → Es un dato editable; se ajusta sin desplegar. Los umbrales salen de la línea base, no de la intuición.
- [La línea base es de una muestra pequeña] → Se declara; los umbrales son de arranque y se revisan cuando crezca el dataset.
- [El gate no corre en cada PR] → Es deliberado: necesita modelos; su sitio es `develop`.

## Open Questions

- Ninguna.