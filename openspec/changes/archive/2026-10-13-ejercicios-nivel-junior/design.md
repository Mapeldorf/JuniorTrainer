# Design

## Context

Ver proposal.md ("Why") para la motivacion. Estado actual relevante:

- Todo el trabajo de redaccion esta en una unica llamada al modelo logico `generator` desde `_draft_candidates()` (`agents/exercises/app/service.py`), con `_SYSTEM_PROMPT` como unica fuente de instrucciones de forma. Ese prompt habla del tipo (`knowledge`/`debug`), del numero exacto de candidatos, de no repetir temas y del formato JSON de salida, pero no dice nada del nivel del alumno ni de la longitud del enunciado.
- La justificacion de una evaluacion se produce en dos pasos, cada uno con una unica llamada al modelo: el agente evaluador (`agents/evaluator/app/service.py`) propone `verdict` + `justification`, y el revisor (`agents/reviewer/app/service.py`) devuelve la version final de esa justificacion. El `verdict` que persiste es siempre el del evaluador; la justificacion que persiste es siempre la del revisor. Ninguno de los dos prompts menciona longitud.
- La salida se valida hoy de forma deterministica solo en lo estructural: en ejercicios, array JSON con exactamente `count` elementos y los tres campos esperados en cada uno; en evaluador/revisor, `verdict` dentro de los tres valores validos y `justification` no vacia. Cualquier incumplimiento lanza la excepcion propia del agente, que el orquestador correspondiente traduce a generacion en estado de error o a evaluacion no completada.
- Limites ya vigentes que condicionan la solucion: en la generacion, 2 minutos por tarea A2A y 5 minutos por generacion completa (requisito "Limites de tiempo de la generacion"); en la evaluacion, que es sincrona dentro de la peticion HTTP del alumno (`answer.verdict` es `NOT NULL`, asi que la fila no puede insertarse antes de tenerlo), cada llamada extra al modelo se nota en lo que el alumno espera.
- Los contratos A2A de entrada/salida no cambian, y los ejercicios ya guardados y las respuestas ya evaluadas son inmutables (`data-authorization`), asi que este change solo puede afectar a lo que se genere o evalue a partir de ahora.
- El flujo de generacion ya tiene revision humana: el tech lead ve los candidatos y decide cuales guarda, asi que la calidad cualitativa no depende solo del agente. El de evaluacion no la tiene: lo que devuelven los dos agentes se persiste tal cual.

## Goals / Non-Goals

**Goals:**

- Que el limite de 50 palabras sea una garantia del sistema (comprobada en codigo) tanto en el enunciado como en la justificacion que se persiste, no una indicacion que el modelo puede ignorar.
- Que el nivel junior quede escrito en el prompt con criterios concretos y comprobables por una persona (un concepto, un fallo, sin redisenos), no como un adjetivo suelto.
- Mantener una sola llamada al modelo por agente en el camino feliz, para no acercarse al limite de 2 minutos por tarea ni alargar la espera del alumno al responder.

**Non-Goals:**

- No se introduce un paso de "simplificacion" ni un agente nuevo para acortar textos.
- No se hace configurable ni el limite de palabras ni el nivel (no hay parametro nuevo en los contratos A2A, ni en el backend, ni en el frontend).
- No se intenta medir automaticamente la dificultad de un candidato ni la calidad de una justificacion: no es verificable de forma deterministica.
- No se cambia quien decide el `verdict` ni el reparto de responsabilidades entre evaluador y revisor.

## Decisions

### 1. El nivel y el tamano se imponen en el prompt de sistema, no con un paso extra

Se reescribe `_SYSTEM_PROMPT` del agente de ejercicios para que describa al destinatario (junior recien incorporado), fije el limite de 50 palabras del enunciado, pida un unico concepto por candidato y acote el codigo de apoyo (un fragmento breve de un solo fichero; exactamente un fallo en `debug`; vacio en `knowledge` cuando no hace falta).

Alternativa descartada: una segunda llamada al modelo que "simplifique" los candidatos ya redactados. Dobla el coste y la latencia de cada generacion contra un limite de 2 minutos por tarea, y resuelve con dos llamadas lo que una instruccion clara resuelve en una.

Alternativa descartada: pedir al modelo un `word_count` en el JSON. Un campo que el propio modelo rellena no es una garantia; contar en Python es gratis y no admite discusion.

### 2. El limite de palabras se valida en codigo, con un unico reintento correctivo

Tras parsear la respuesta, el agente cuenta las palabras del texto limitado (secuencias separadas por espacios en blanco, es decir `len(texto.split())`) contra una constante de modulo con valor 50. Si se pasa, se repite la llamada una sola vez anadiendo a la conversacion la respuesta anterior y un mensaje que nombra lo que se pasaba y por cuanto. Si tras ese reintento sigue habiendo incumplimientos, se lanza la excepcion propia del agente (`ExerciseGenerationError`, `EvaluationError`, `ReviewError`), que deja la generacion en error o la evaluacion sin completar por las reglas ya existentes.

Por que un reintento y no otra cosa:

- *Truncar el texto a 50 palabras*: descartado, deja enunciados y justificaciones cortados sin sentido, y en el enunciado rompe la correspondencia con la respuesta esperada.
- *Fallar directamente sin reintento*: descartado, convierte un desliz de una palabra en una generacion perdida o en un intento de respuesta rechazado.
- *Reintentar hasta que cumpla*: descartado, el numero de llamadas deja de estar acotado; en la generacion el limite de 2 minutos por tarea pasaria a ser la unica red de seguridad, y en la evaluacion el alumno esperaria sin cota.

En el agente de ejercicios el reintento se aplica a la peticion completa (los `count` candidatos), no solo al candidato que se pasaba: el modelo devuelve el array entero y mezclar candidatos de dos respuestas distintas reabriria la posibilidad de temas repetidos entre ellos.

### 3. La validacion estructural y la de longitud se separan del guardado en memoria

`generate_exercises()` ya escribe el historial de enunciados (`save_statements`) solo despues de que `_draft_candidates()` devuelva candidatos validos. Como la comprobacion de longitud y el reintento viven dentro de `_draft_candidates()`, los enunciados demasiado largos de un primer intento fallido nunca entran en el historial, y el historial sigue conteniendo solo enunciados que cumplen el limite.

### 4. Los criterios cualitativos se verifican a mano, con scripts

"Un unico concepto", "nivel junior" y "la justificacion sigue siendo util en 50 palabras" no se pueden comprobar en codigo. Se anade un script `verify_*` por agente, al estilo de los `verify_*.py` que ya existen: lanzan llamadas reales contra el modelo, imprimen cada texto con su recuento de palabras y fallan si alguno se pasa, dejando a la vista el contenido para juzgar el nivel y la utilidad por lectura. En la generacion la decision final sigue siendo del tech lead, que ya revisa los candidatos antes de guardarlos.

### 5. Los agentes web y de codigo se quedan como estan

El resumen del agente web y los fragmentos del agente de codigo son material de referencia, no el enunciado. Los fragmentos ya estan acotados a 12 lineas, compatible con "un fragmento breve de un solo fichero". Tocar esos prompts ampliaria el alcance sin necesidad demostrada.

### 6. El limite de la justificacion lo garantizan los dos agentes, cada uno sobre su propia salida

El requisito habla de la justificacion que se persiste, y la que se persiste es la del revisor. Por eso el limite se aplica en los dos sitios:

- El evaluador pide y valida 50 palabras como maximo en la justificacion que propone, con el reintento de la decision 2. Asi el revisor no recibe un parrafo que tenga que resumir.
- El revisor pide y valida 50 palabras como maximo en la version final, y su prompt le indica explicitamente que, si la justificacion propuesta llegara mas larga, su trabajo incluye acortarla. Es el ultimo punto antes de persistir, asi que es el que convierte el limite en garantia.

Alternativa descartada: acotar solo al evaluador. El revisor puede reescribir la justificacion y la que persiste es la suya, asi que el limite no se sostendria.

Alternativa descartada: validar el limite en `backend/app/answer_orchestrator.py` en vez de dentro de los agentes. El orquestador no puede corregir nada (solo volver a lanzar la tarea entera), y dejaria a los agentes devolviendo salidas que incumplen su propio contrato; validar donde se genera el texto mantiene el backend sin cambios.

Consecuencia aceptada: si el incumplimiento persiste tras el reintento, la respuesta del alumno no se persiste y recibe un error. Es exactamente el camino que ya existe para cualquier fallo de la evaluacion ("La evaluacion no puede completarse"), es recuperable (no queda nada escrito, el alumno reintenta) y no deja datos a medias.

### 7. El contador de palabras se duplica por agente, no se extrae a una libreria comun

Cada agente es un servicio independiente con su propio `app/` y su propio `requirements.txt`; no hay paquete compartido entre ellos, y `_parse_json` ya esta duplicado en los tres con un comentario que lo dice explicitamente. Un contador de palabras de dos lineas sigue el mismo criterio: duplicarlo es mas barato que introducir una dependencia comun solo para esto, y cada agente conserva su propia constante si algun dia los limites divergen.

## Risks / Trade-offs

- **El modelo cumple las 50 palabras pero mete la dificultad en el codigo de apoyo** (un fragmento enorme, varios fallos) → el requisito "Codigo de apoyo acotado" lo cubre en el prompt, y el script de verificacion imprime tambien el codigo para revisarlo por lectura.
- **Mas generaciones en error y mas respuestas rechazadas por el limite duro** → el reintento correctivo absorbe el caso normal; si en la verificacion se observa que el reintento falla a menudo, subir el numero de reintentos es un cambio de una constante, no de diseno.
- **El reintento anade una llamada al modelo** → en la generacion cabe con holgura en los 2 minutos por tarea; en la evaluacion alarga la espera del alumno, pero solo cuando hay incumplimiento y solo una vez.
- **Una justificacion de 50 palabras puede quedarse corta para una respuesta muy equivocada** → es el precio de un texto que un junior lee entero; el prompt prioriza decir que falta o que esta mal antes que explicar la teoria, y el tech lead sigue viendo el enunciado y la respuesta esperada completos en el progreso del bloque.
- **Enunciados mas cortos pueden perder contexto necesario** (el alumno no sabe sobre que fichero o tecnologia se le pregunta) → el codigo de apoyo y la respuesta esperada no cuentan para el limite, asi que el contexto imprescindible puede ir en el fragmento de codigo en vez de en el enunciado.
- **Lo ya guardado sigue siendo largo** (ejercicios definitivos y respuestas ya evaluadas) → son inmutables por diseno; el tech lead puede eliminar logicamente un ejercicio y regenerar. No se migra nada.

## Migration Plan

Sin migracion de datos: no hay cambios de esquema, ni de contrato A2A, ni de API HTTP. El despliegue es reconstruir las imagenes de los tres agentes afectados (`docker compose build agent-exercises agent-evaluator agent-reviewer` + `up -d`). El rollback es revertir el commit: las generaciones y evaluaciones posteriores vuelven al comportamiento anterior, y lo ya producido no se ve afectado.
