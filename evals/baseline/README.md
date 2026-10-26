# Informes de referencia de la suite de evaluación

Los informes que sostienen las cifras del capstone. Cada ejecución escribe su
informe en `evals/results/`, que git ignora; aquí se versionan solo los que el
documento cita, para que cualquiera pueda comprobar las cifras sin volver a
ejecutar la suite, que en modo real cuesta dinero y necesita el stack levantado.

| Carpeta | Informes | Qué sostiene |
|---|---|---|
| `primario/` | `20261024T135007Z`, `20261024T135820Z`, `20261024T140622Z` | Las tres ejecuciones completas con los modelos primarios (§5.7) y la línea base de la que salen los umbrales de `evals/thresholds.json` (§5.8) |
| `respaldo/` | `20261024T163846Z`, `20261024T164648Z` | Las dos ejecuciones completas con los cuatro roles resueltos al respaldo de Hugging Face: comparativa primario/respaldo (§5.7, riesgo 8) |
| `red-teaming/` | `20261024T122329Z` | El ejercicio de red teaming (§6.5 y `capstone/red-teaming/informe.md`) |
| `razonamiento/` | `20261024T111510Z` (sin ajuste), `111757Z` (`off`), `112205Z` (`effort=low`), `112537Z` (`effort=medium`), `113045Z` (`effort=high`) | El experimento de coste del razonamiento (§3.7, apartado 14) |
| `costes/` | `20261024T060409Z`, `061748Z`, `063002Z` y su informe de costes `20261024T063002Z-real-costes.{json,md}` | Los costes por agente, por operación y por campaña (§3.7). El informe de costes cita los tres de entrada con su ruta original en `evals/results/` |
| `juez/` | `20261024T183305Z` (κ 0,312, rúbrica sin anclar), `20261024T185544Z` (κ 0,475, rúbrica anclada) | La calibración del juez de contenido (§5.6) |

## Lo que se ha redactado

El agente de código se midió contra un repositorio **privado**
(`EVALS_REAL_REPO`), y este repositorio es público. En los informes con casos
reales del agente de código, el contenido que procede de ese repositorio se
sustituye por `[redactado: repositorio privado]`:

- `result.summary`, y `file`, `code` y `note` de cada fragmento;
- las rutas elegidas (`probe.picks`, `probe.invalid_picks`);
- el mensaje de error, si lo hay.

Se conservan los números (`start_line`, tokens, coste, duración), las
tecnologías detectadas y el bloque `agents` completo, que es de donde salen
todas las métricas: es idéntico al del informe original. Los demás informes
se copian sin cambios.

## Cómo añadir uno

Ejecuta la suite (`evals/README.md`), copia el informe de `evals/results/` a la
carpeta que corresponda y añádelo a esta tabla. Si incluye casos reales del
agente de código contra un repositorio que no sea público, redacta antes su
contenido como se describe arriba.
