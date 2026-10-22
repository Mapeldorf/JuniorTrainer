# Proposal

## Why

Hoy no hay forma de saber si un cambio de modelo o de prompt empeora el sistema (capstone §5.4, §8). Los 19 `verify_*.py` de los agentes comprueban comportamiento del código, pero son scripts manuales, sin dataset versionado, sin métricas agregadas y sin forma de comparar modelo primario y fallback. Faltan los niveles 2 (automatizar los verificadores) y 3 (dataset dorado con métricas deterministas) de la pirámide de evaluación, y las tablas de §5.7 no se pueden rellenar sin ellos.

## What Changes

- Un **arnés de evaluación** (`evals/`) que ejecuta los agentes evaluador, revisor, validador y de ejercicios sobre un **dataset dorado** versionado en el repositorio y calcula métricas deterministas, sin ningún juicio humano ni de modelo en tiempo de ejecución.
- Cuatro conjuntos de datos: generación, evaluación, validación y adversarial (este último solo como casos de prueba permanentes; el red teaming es otro change).
- Métricas de capstone §5.5: validez de salida, adherencia a límites, tasa de activación del reintento correctivo, conformidad de cardinalidad, exactitud del veredicto (matriz de confusión y κ de Cohen), precisión del gate del validador, detección de duplicados, no repetición de temas, falsos positivos de guardarraíl y latencia p50/p95/p99.
- **Dos modos de ejecución**: *simulado* (modelo falso guionizado por el dataset, sin red ni credenciales, apto para CI) y *real* (contra LiteLLM con el stack levantado, manual o en staging, con coste).
- Informe estructurado (JSON + resumen legible) por ejecución.
- Un job de CI que ejecuta el modo simulado en los PR que toquen `agents/` o `evals/`.

### Supuestos (el usuario no concretó el alcance; se adoptan las opciones recomendadas)

- **Solo métricas deterministas.** El juez LLM (§5.6) es un change aparte: necesita calibración contra etiquetas humanas.
- **Cubre cuatro agentes:** evaluador, revisor, validador y ejercicios. Los agentes web y de código dependen de Tavily y de la API de GitHub y quedan fuera; siguen cubiertos por sus `verify_*.py`.
- **Las etiquetas del dataset las redacta quien implementa el change**, a partir de lo que piden los prompts y de los casos ya usados en los verificadores. Deben revisarse por el tech lead antes de tomar los números como referencia (de ahí que el κ de Cohen del primer informe se interprete con esa cautela).
- **Sin umbrales de bloqueo en modo real.** El informe solo mide; fijar umbrales es el punto 4 de §5.3 y necesita la línea base que este change produce.

### Fuera de alcance

Juez LLM (§5.6), red teaming con `promptfoo`/`garak` (§6.5), costes (§3.8), plataforma de despliegue (§5.2), `ruff`/`mypy` y el resto del CI/CD de §5.3, cambios en el código de producción de los agentes.

## Capabilities

### New Capabilities

- `agent-evaluation`: evaluación reproducible de los agentes sobre un dataset dorado versionado, con métricas deterministas, modo simulado y modo real, e informe estructurado.

### Modified Capabilities

Ninguna.

## Impact

- Directorio nuevo `evals/` en la raíz (arnés, dataset, informes); ningún cambio en `agents/*/app`, backend ni frontend.
- `.github/workflows/ci.yml`: un job nuevo con filtro por rutas.
- Dependencias: solo biblioteca estándar en el arnés; en CI se instalan los `requirements.txt` de cada agente evaluado.
- Alimenta §5.5 y §5.7 y el Anexo E del capstone; la ejecución en modo real consume presupuesto de las virtual keys de cada agente.
