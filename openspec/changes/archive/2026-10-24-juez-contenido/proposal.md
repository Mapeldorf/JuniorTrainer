# Proposal

## Why

Las métricas deterministas de §5.5 miden el **contrato** de la generación (formato,
límites de palabras, cardinalidad, solapamiento de temas), pero no la **calidad
pedagógica** del contenido: si el enunciado es de nivel junior, si es resoluble con lo
que se entrega, si trata **un solo** concepto, o si el fallo del ejercicio `debug` es
real y localizable. El prompt del agente de ejercicios **pide** esas propiedades (change
`ejercicios-nivel-junior`), pero —a diferencia del límite de palabras— el código **no
puede verificarlas**; hoy la única comprobación es la aprobación humana. Falta el nivel
4 de la pirámide de §5.4 (capstone §5.6): un juez LLM **offline** que dé una señal
**repetible** de esas propiedades, para detectar cuándo un cambio de prompt o de modelo
degrada el contenido aunque el contrato siga cumpliéndose.

## What Changes

- Un **instrumento de juicio offline** en `evals/` —**no** un agente ni un servicio
  A2A—: puntúa ejercicios con una **rúbrica de cinco criterios**, con justificación
  obligatoria, usando un **modelo frontier distinto** de los cuatro de producción
  (evita el sesgo de autopreferencia).
- Un **conjunto de calibración versionado** `evals/datasets/judge.jsonl` (los ejercicios
  a puntuar) y un fichero de **puntuaciones humanas** separado (la calibración se hace
  a ciegas).
- **Calibración contra el humano**: concordancia juez-vs-humano (κ de Cohen) por
  criterio. Si es baja, se corrige la rúbrica, no el resultado.
- Un alias `judge` en `infra/litellm/config.yaml` (modelo por variable de entorno), sin
  tocar el código de ningún agente.
- Un informe del juez en `evals/results/`, con la rúbrica usada.

### Supuestos

- **Alcance mínimo.** Una rúbrica, una muestra pequeña, ejecución offline. No hay
  comparación entre modelos juez ni integración en el flujo de producción.
- El juez **no sustituye** la aprobación del tech lead (§4.6): es un instrumento de
  regresión, y así se declara.

### Fuera de alcance

- Umbrales sobre las puntuaciones del juez, ejecutarlo en CI como *gate*, red teaming
  (§6.5), y cualquier cambio en el código de producción de los agentes.

## Capabilities

### New Capabilities

- `content-judging`: juicio offline de la calidad pedagógica del contenido generado con
  una rúbrica acotada, calibrado contra puntuaciones humanas.

### Modified Capabilities

Ninguna.

## Impact

- Directorio `evals/` (módulo del juez, conjunto de calibración, README); `infra/litellm/config.yaml`
  y `.env.example` (alias `judge`); ningún cambio en `agents/*/app`, backend ni frontend.
- Alimenta §5.6 del capstone. El juez no escribe en la base de datos ni toca al alumno.