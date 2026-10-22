# Proposal

## Why

`openspec validate --specs` emite un aviso informativo ("Requirement text is very long (>500 characters)") en tres requisitos vigentes: uno en `exercise-catalog`, uno en `frontend-security-headers` y uno en `technology-validation`. Cada uno mezcla en un solo párrafo la regla principal con detalle y aclaraciones que ya tienen (o deberían tener) su escenario. Las specs se citan como evidencia de calidad en el capstone, y conviene que cumplan la convención "un comportamiento por requisito, el detalle en escenarios".

## What Changes

- Acortar la descripción de tres requisitos a 500 caracteres o menos, conservando su regla normativa principal.
- Mover el detalle sobrante a los escenarios, ajustando uno de ellos en `frontend-security-headers` y otro en `technology-validation` para que no se pierda ninguna garantía.
- No cambia ningún comportamiento del sistema ni ningún escenario existente se elimina.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `exercise-catalog`: requisito "Listar y buscar ejercicios definitivos"; solo se reescribe la descripción (656 → menos de 500 caracteres), los escenarios no cambian.
- `frontend-security-headers`: requisito "Content-Security-Policy estricta sin inline"; la prohibición de orígenes de fuentes externas pasa a precisarse en su escenario.
- `technology-validation`: requisito "Validacion de tecnologias como puerta previa a la generacion"; la aclaración de que el validador no compara contra el catálogo pasa a precisarse en su escenario.

## Impact

- Solo ficheros de `openspec/specs/` (tras archivar). Ningún código de backend, agentes, frontend ni infraestructura.
- Efecto observable: `openspec validate --specs` deja de emitir los tres avisos.
- El recuento de cambios archivados del capstone sube en uno.
