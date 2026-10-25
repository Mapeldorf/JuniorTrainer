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

Cifras verificadas contra el código el 22 de octubre de 2026: timeouts en capas,
límites de ritmo, tamaño de cuerpo, presupuestos de operaciones, TTL de memorias,
presupuestos de las virtual keys, topes de entrada, pre-filtro del validador,
triggers, modelos por rol y los siete prompts del Anexo A.

## Estado

Redactadas las secciones que se apoyan en lo ya implementado. Quedan pendientes,
marcadas como tales dentro del propio documento:

| Sección | Qué falta | Depende de |
|---|---|---|
| §5.2 | Presupuesto de infraestructura | Decidirlo |
| §5.3 | Lint/`mypy`, tests de backend y los `verify_*.py` automatizados (el gate de evals ya existe) | Implementarlo |
| §5.8 | Montar el cuadro de mando y sus alertas | Infraestructura (los umbrales ya están especificados) |
| §6.5 | Cobertura restante del red teaming: resistencia del modelo en web y código (repo de prueba), y objetivos 7 y 9 | Extender el arnés |
| §6.6 | Trabajo de cumplimiento: RAT, base jurídica, transparencia, acuerdos de encargado y retención | Cumplimiento |

## Generar el PDF

Con [Pandoc](https://pandoc.org/) y un motor LaTeX instalado. Los diagramas
Mermaid requieren el filtro `mermaid-filter` (`npm i -g mermaid-filter`):

```bash
pandoc capstone/juniortrainer-capstone.md -o capstone/juniortrainer-capstone.pdf --toc --toc-depth=3 --number-sections -V geometry:margin=2.5cm -V linkcolor=blue -F mermaid-filter
```

Sin el filtro de Mermaid, los diagramas salen como bloques de código. Alternativa
sin LaTeX, pasando por HTML:

```bash
pandoc capstone/juniortrainer-capstone.md -o capstone/juniortrainer-capstone.html --toc --standalone --embed-resources -F mermaid-filter
```
