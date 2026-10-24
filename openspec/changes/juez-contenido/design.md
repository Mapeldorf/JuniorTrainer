# Design

## Context

Ver `proposal.md`. Lo comprobado en el código y en la suite existente:

- La suite de §5.5 (`evals/`) mide el contrato de forma determinista; el agente de
  ejercicios **pide** el nivel junior y la unicidad de concepto en su prompt
  (`agents/exercises/app/service.py`) pero solo **garantiza en código** el límite de
  palabras y el nombre, no esas propiedades.
- El arnés ya sabe llamar a LiteLLM en modo real (`evals/agent_runner.py`) y ya tiene
  `cohen_kappa` genérico por etiquetas (`evals/metrics.py`), reutilizable para las
  puntuaciones del juez.
- Todos los agentes hablan con LiteLLM por un alias lógico; el alias del juez sigue esa
  misma regla para no atar la rúbrica a un proveedor.

## Goals / Non-Goals

**Goals:**
- Una señal **repetible** de la calidad pedagógica del contenido, comparable entre
  ejecuciones y atribuible a un cambio de prompt o de modelo.
- Que esa señal esté **acotada** (rúbrica) y **calibrada** (κ contra un humano), para que
  sea un instrumento y no una opinión con formato de métrica.

**Non-Goals:**
- Sustituir la aprobación humana, correr en producción, fijar umbrales, comparar varios
  modelos juez, o juzgar calidad más allá de los cinco criterios de la rúbrica.

## Decisions

**1. Es un instrumento de `evals/`, no un agente.** El juez vive en `evals/judge.py`,
usa solo biblioteca estándar (llama a LiteLLM por HTTP, igual que la comprobación previa
del modo real) y **no** se despliega como servicio A2A. *Alternativa descartada:* un
séptimo agente A2A; añadiría un servicio, credencial y contrato para algo que no está en
el camino del usuario.

**2. El modelo juez es un alias `judge` de LiteLLM, distinto de los de producción.** Se
resuelve por variable de entorno (`JUDGE_MODEL`), de modo que cambiar de juez es cambiar
una variable, sin tocar código. El criterio es que **no** sea ninguno de los cuatro roles
de producción, para evitar el sesgo de autopreferencia. El juez se autentica contra
LiteLLM con su **propia virtual key** (`AGENT_JUDGE_LITELLM_KEY`), restringida al alias
`judge` y aprovisionada como las de los agentes: es lo que exige el principio de
`litellm-agent-keys` —cada consumidor del proxy con su credencial propia, ninguna con la
master key— y mantiene su uso atribuible y revocable por separado.

**3. Rúbrica de cinco criterios, cada uno 0–2, con justificación obligatoria.** Los cinco
criterios son la traducción directa de lo que piden los prompts (§5.6):
unicidad de concepto, autosuficiencia, nivel (junior), calidad del fallo (`debug`) y
utilidad de la justificación. «Calidad del fallo» no aplica a `knowledge` y se informa
como `null`. La salida es JSON validado; si no cumple, se reintenta **una vez** (misma
regla que los agentes) y si vuelve a fallar, el ejercicio cuenta como no juzgado, no como
puntuación.

**4. Conjunto de calibración versionado y puntuación humana separada.** `evals/datasets/judge.jsonl`
lleva los ejercicios a puntuar (no la puntuación). La humana vive en un fichero aparte
que se rellena **después** y **a ciegas** de la del juez: si el humano viera la nota del
juez, la calibración no mediría nada. El conjunto es una **curación para calibrar** —un
abanico que va de ejercicios claramente buenos a claramente malos— y no una muestra
aleatoria: para calibrar una rúbrica hace falta que discrimine.

**5. Calibración por κ de Cohen por criterio.** Se reutiliza `cohen_kappa` con las
etiquetas de puntuación (0, 1, 2). Se informa por criterio y global. *Criterio de
actuación:* si la concordancia es baja, se **corrige la rúbrica**, no el resultado.

**6. Informe en `evals/results/`.** Mismo patrón que la suite: JSON + resumen legible, con
la rúbrica y el modelo juez registrados. No bloquea nada; solo mide.

## Risks / Trade-offs

- [Un juez LLM es ruidoso y sensible al prompt] → Rúbrica acotada, calibración obligatoria
  y valor **relativo** (detector de regresión), nunca una nota absoluta que se muestre.
- [El conjunto de calibración es pequeño y curado] → Se declara; crece sin cambiar el juez.
- [El humano conoce a su equipo y puede sesgarse] → La calibración se hace a ciegas y se
  informa el número de casos junto al κ.
- [El juez podría solaparse con la aprobación humana] → No la sustituye; se declara como
  límite.

## Open Questions

- Qué modelo frontier concreto se usa como juez: se decide al ejecutarlo y se registra en
  el informe; no afecta a la spec ni a las tareas.