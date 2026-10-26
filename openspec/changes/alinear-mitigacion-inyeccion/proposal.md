# Proposal

## Why

La especificacion `prompt-injection-mitigation` exige la comprobacion automatizada de inyeccion sobre las llamadas de evaluador, revisor y validador (deployments principal y de respaldo), pero la postura real del sistema desde `guardarrailes-por-capas` solo la aplica al validador y su respaldo: la medicion sobre las 15 respuestas reales almacenadas dio 1 falso positivo, por lo que encenderla en evaluador y revisor impediria corregir una respuesta de cada quince. La re-activacion queda condicionada a subir el umbral de *enforcement* en la plataforma de Lakera y remedir (riesgo 1 del registro del capstone). La spec y el codigo contradicen esa postura, y hay que alinearlos. Ademas, el prompt del agente de ejercicios es el unico que recibe material derivado de contenido no confiable —los resumenes del web y del repositorio— sin delimitadores ni instruccion defensiva: una inyeccion que burle al agente web o al de codigo viajaria hoy desnuda hasta el redactor.

## What Changes

- El requisito de bloqueo automatizado pasa a exigir la comprobacion **solo** sobre los deployments del validador (primario y respaldo), reflejando la configuracion real.
- Nuevo requisito: la comprobacion automatizada SHALL permanecer desactivada en evaluador y revisor, y su activacion SHALL quedar supeditada a una recalibracion previa documentada (subir el umbral de *enforcement* en la plataforma de Lakera y remedir la tasa de falsos positivos sobre el corpus de respuestas reales redactadas).
- Nuevo requisito: el prompt del agente de ejercicios SHALL envolver el material de origen —resumen de documentacion y resumen/fragmentos de repositorio— en delimitadores explícitos de dato, con una instruccion defensiva adaptada.
- Ajuste de los escenarios del requisito modificado para describir la postura actual (el bloqueo de una respuesta de alumno es el comportamiento futuro condicionado, no el vigente).

## Capabilities

### New Capabilities

Ninguna: la conducta ya tiene su capacidad (`prompt-injection-mitigation`) y no se introduce una frontera nueva.

### Modified Capabilities

- `prompt-injection-mitigation`: el alcance del bloqueo automatizado (solo validador, con re-activacion condicionada para evaluador y revisor) y la mitigacion por instruccion del prompt de ejercicios.

## Impact

- `infra/litellm/config.yaml`: **sin cambios** —el change alinea la spec al codigo, no el codigo a la spec; la vinculacion de `lakera-guard-block` al validador y su respaldo ya es la postura vigente.
- `agents/exercises/app/service.py`: delimitadores de dato y frase defensiva en la composicion del prompt del redactor.
- `evals/agent_runner.py`: la invariante de delimitadores del arnes se extiende a los casos del agente de ejercicios.
- Documentacion del capstone: Anexo A.4 (prompt integro), §3.6 (la excepcion del septimo prompt deja de existir) y §6.3 (los «seis prompts» con frase defensiva pasan a siete).
- La medicion previa a cualquier activacion futura en evaluador y revisor queda gobernada por la secuencia de §6.5 (change propio aparte cuando se recalibre).