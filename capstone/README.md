# Entregable capstone

Documentación de la entrega del proyecto capstone del Máster en IA Generativa
Avanzada, sobre JuniorTrainer.

| Fichero | Qué es |
|---|---|
| `juniortrainer-capstone.md` | **El entregable.** Documento de especificación y diseño técnico |
| `esquema-documento.md` | Documento de trabajo: índice anotado con el estado de cada sección |

## Fuentes

El documento se apoya en **el código y `openspec/specs/`** como fuente de verdad.
Los ficheros de `docs/` (ignorados por git, temporales) se usaron solo como guía de
estructura: contienen al menos tres afirmaciones desactualizadas —número de tablas,
polling del frontend y lecturas directas del frontend a Supabase— que no se han
propagado.

Cifras verificadas contra el código y los informes locales el 26 de octubre de
2026: timeouts en capas, límites de ritmo, tamaño de cuerpo, presupuestos de
operaciones, TTL de memorias, presupuestos y ritmo de las virtual keys, topes de
entrada, pre-filtro del validador, triggers, modelos por rol, los siete prompts del
Anexo A, los cinco jobs del CI (168 tests del arnés), los 19 verificadores de
agentes, los umbrales del gate y las cifras de §5.7 y del informe de red teaming.

## Estado

Revisión global completa (portada y resumen, «cómo leer», §1–§8 y Anexos A–G), en
la rama `docs/capstone-revision-global`. **Re-revisión por tramos completada**
(portada, resumen y «cómo leer»; §1, §2 y §3 completos, y §4.1–§4.8), en las ramas
`docs/capstone-rerevision-*` y los PRs #123–#127. Las cifras de cabecera quedan
reverificadas: 29 capacidades, 62 cambios, 126 casos del dataset en seis conjuntos
más 10 del juez, y 25 controles de seguridad.

**Versión 1.1, condensada** (rama `docs/capstone-condensado`): de unas 48.000 a unas
22.600 palabras de texto. Los capítulos de la materia del máster —modelos, agentes,
evaluación y seguridad de LLM— conservan el mayor peso; el contexto, el despliegue y
el cumplimiento se resumen. Los prompts del Anexo A y las referencias se conservan
íntegros. El Anexo G es la guía de uso con once capturas de la aplicación
(`img/`). En total, unas **45 páginas** A4 a 10 pt. Quedan pendientes, marcadas como
tales dentro del propio documento:

| Sección | Qué falta | Depende de |
|---|---|---|
| §5.2 | Elegir proveedor (el presupuesto está estimado en §3.7) y aprovisionar `develop` | Infraestructura |
| §5.9 | Verificar qué hace LiteLLM cuando Lakera no responde (el runbook lo declara sin verificar) | Probarlo contra el stack |
| §5.3 | Lint/`mypy`, tests de backend y los `verify_*.py` automatizados (el gate de evals ya existe); protección de rama que lo haga obligatorio | Implementarlo |
| §5.8 | Montar el cuadro de mando y sus alertas | Infraestructura (los umbrales ya están especificados) |
| §6.4 | Reactivar Lakera en evaluador y revisor (riesgo 1) y gestor de secretos por servicio (riesgo 7) | Change propio / infraestructura |
| §6.5 | Cobertura restante del red teaming: resistencia del modelo en web y código (repo de prueba), y objetivos 7 y 9 | Extender el arnés |
| §6.6 | El borrador de cumplimiento (RAT, base jurídica, información, encargados, retención, EIPD) está escrito; falta su revisión jurídica y un procedimiento de supresión de los datos de un alumno | Cumplimiento / implementarlo |
| §6.7 | Impugnación de valoraciones; documentar la evaluación del artículo 6.3 del Reglamento de IA; verificar la certificación DPF de los proveedores de la lista de enrutado y decidir sobre el respaldo de Hugging Face (la política de enrutado ya está, change `enrutado-proveedores-openrouter`) | Change propio / cumplimiento |
| §5.7 | La línea base vigente (`evals/baseline/enrutado/`, 27 de octubre) muestra la cola de latencia más larga con la política de enrutado: vigilarla y, si hace falta, ajustar la lista de proveedores o los timeouts | Medición en producción |

## Generar el PDF

Con [Pandoc](https://pandoc.org/) y un motor LaTeX instalado. Los diagramas
Mermaid requieren el filtro `mermaid-filter` (`npm i -g mermaid-filter`). El cuerpo va
a 10 pt con márgenes de 2 cm, y `pdf-header.tex` reduce tablas y código a
`\footnotesize`; con esa maqueta el documento ronda las 45 páginas. Las capturas
de `img/` se resuelven en relación con el documento, así que el comando se lanza
con `--resource-path=capstone`. Las secciones ya
llevan su número en el título, así que no se usa `--number-sections`:

```bash
pandoc capstone/juniortrainer-capstone.md -o capstone/juniortrainer-capstone.pdf --toc --toc-depth=2 -V fontsize=10pt -V geometry:margin=2cm -V linkcolor=blue -H capstone/pdf-header.tex --resource-path=capstone -F mermaid-filter
```

Sin el filtro de Mermaid, los diagramas salen como bloques de código. Alternativa
sin LaTeX, pasando por HTML:

```bash
pandoc capstone/juniortrainer-capstone.md -o capstone/juniortrainer-capstone.html --toc --standalone --embed-resources -F mermaid-filter
```
