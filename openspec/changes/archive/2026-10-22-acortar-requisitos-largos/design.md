# Design

## Context

Ver `proposal.md`. El validador de OpenSpec avisa (nivel `INFO`) cuando la descripción de un requisito, el texto entre `### Requirement:` y su primer `#### Scenario:`, supera los 500 caracteres. Hoy lo hacen tres requisitos de specs vigentes. No hay código afectado: es un cambio de redacción de specs.

## Goals / Non-Goals

**Goals:**
- Dejar las tres descripciones por debajo de 500 caracteres.
- No perder ninguna garantía: todo lo que se quita de la descripción debe seguir expresado, de forma comprobable, en un escenario.

**Non-Goals:**
- Cambiar comportamiento del sistema o añadir requisitos nuevos.
- Partir requisitos en varios. Se descarta para no alterar la estructura ni el nombre de requisitos que otras specs y documentos citan.
- Tocar otros requisitos largos o el contenido de otras specs.

## Decisions

**1. Recortar la descripción y conservar una frase normativa por regla.** En `exercise-catalog` los datos incluidos por ejercicio y la paginación con total se resumen en una sola frase con SHALL; el detalle (filtros combinados, páginas fuera de rango, ejercicios de generaciones cerradas) ya estaba en escenarios. Alternativa descartada: dejar solo la primera frase. Habría quitado el SHALL de la paginación y de los datos incluidos, que son parte del contrato.

**2. Mover lo que no estaba en un escenario al escenario más cercano**, en lugar de crear escenarios nuevos:
- `frontend-security-headers`: la prohibición de orígenes de fuentes externas se refuerza en el escenario "Sin origenes de fuentes externas".
- `technology-validation`: la aclaración de que el validador no compara contra el catálogo al validar una generación se añade al escenario "Tecnologia ya existente en el catalogo". La regla complementaria (la comparación sí se hace en un alta) ya vive en el requisito "Comprobacion semantica de duplicados contra el catalogo".
- `exercise-catalog`: la precisión "independientemente de si la generación sigue pendiente o ya cerrada" se mantiene en el escenario de generación cerrada.

**3. Usar `MODIFIED` con el requisito completo, escenarios incluidos.** La guía del flujo recomienda no reescribir texto de un requisito modificado solo para cumplir la longitud. Aquí es justo el objetivo declarado del cambio y el delta incluye el bloque entero, para que el archivado no pierda ningún escenario.

## Risks / Trade-offs

- [Se debilita sin querer una garantía al recortar] → Cada frase eliminada se comprueba contra un escenario; los escenarios de `exercise-catalog` quedan idénticos y los otros dos solo ganan una cláusula `AND`.
- [El texto normativo en escenarios es menos visible que en la descripción] → Aceptable: es la convención del proyecto y la que busca el aviso.
- [El cambio añade una entrada al archivo por un aviso de estilo] → Se asume: deja trazabilidad y mantiene `openspec validate --specs` limpio.
