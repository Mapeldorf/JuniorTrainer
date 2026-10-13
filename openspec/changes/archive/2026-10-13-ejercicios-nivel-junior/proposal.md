# Proposal

## Why

Los candidatos que redacta hoy el agente de ejercicios (`agents/exercises`) salen demasiado largos y demasiado dificiles: su prompt solo pide un enunciado "claro y autocontenido" en espanol, sin decir nada del nivel del alumno ni del tamano del enunciado o del codigo de apoyo, asi que el modelo tiende a proponer ejercicios de varios pasos, con varios conceptos a la vez y enunciados de parrafos enteros. El publico real de la plataforma es un desarrollador junior recien incorporado a un proyecto: un ejercicio que pide redisenar o refactorizar no le sirve, y un enunciado largo es por si solo una barrera. Nada en el sistema impide hoy ese resultado, porque ninguna regla de la capacidad `exercise-generation` habla del nivel ni del tamano de un candidato.

El mismo problema afecta al otro texto que el alumno junior lee: la justificacion de su evaluacion. El prompt del agente evaluador (`agents/evaluator`) le pide explicar "con precision" sin ningun limite de longitud, y el del revisor (`agents/reviewer`) le pide "la MEJOR version" de esa justificacion, que tambien puede alargarla. Un alumno que acaba de leer un enunciado de 50 palabras no deberia recibir a cambio un parrafo largo de valoracion.

## What Changes

- La capacidad `exercise-generation` gana un requisito nuevo sobre el **nivel y el tamano** de todo candidato: orientado a un junior recien incorporado (un unico concepto, resoluble leyendo lo que se le da, sin redisenos ni refactors ni recorridos de varios ficheros) y con el enunciado limitado a **50 palabras como maximo**.
- La capacidad `answer-evaluation` gana el mismo limite para la **justificacion**: la que propone el agente evaluador y la revisada que finalmente se persiste SHALL tener **50 palabras o menos**. El limite se aplica a la justificacion que persiste, no solo a la del evaluador: si solo se acotara la suya, el revisor podria alargarla y el alumno seguiria leyendo un parrafo.
- Ese limite pasa a ser una garantia del sistema, no una sugerencia al modelo: cada agente cuenta las palabras de lo que devuelve y, si se pasa, reintenta **una** vez indicando al modelo que acorte; si tras ese reintento sigue pasandose, la tarea del agente falla y se aplican las reglas de fallo ya existentes de cada flujo (generacion en error; evaluacion no completada, sin persistir ninguna respuesta).
- El codigo de apoyo tambien se acota (como mucho un fichero y un fragmento corto; en `debug`, exactamente un fallo y de los que un junior encuentra leyendo), para que la dificultad no se cuele por el codigo cuando el enunciado ya es breve.
- Los prompts de sistema de los tres agentes afectados (`agents/exercises`, `agents/evaluator`, `agents/reviewer`) y sus Agent Cards se reescriben en consecuencia; se anaden scripts de verificacion manual del limite, al estilo de los `scripts/verify_*.py` que ya tienen los agentes.
- Fuera de alcance: no se anade ningun selector de nivel o dificultad en API ni frontend (el nivel junior es el unico que la plataforma contempla), no se tocan los prompts de los agentes web y de codigo, y no se reescriben los ejercicios ya guardados ni las respuestas ya evaluadas (son inmutables por `data-authorization`).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities
- `exercise-generation`: se anade el requisito "Nivel y tamano de los ejercicios candidatos" (enunciado de 50 palabras como maximo, alcance de junior recien incorporado, codigo de apoyo acotado) y la regla de que un enunciado que se pasa del limite se reintenta una vez y, si persiste, hace fallar la generacion.
- `answer-evaluation`: se anade el requisito de que la justificacion que se persiste con una respuesta evaluada tenga 50 palabras o menos, con el mismo reintento unico y, si persiste el incumplimiento, el camino de error ya existente ("La evaluacion no puede completarse": no se persiste nada y el alumno puede reintentar).

## Impact

- `agents/exercises/app/service.py`: nuevo prompt de sistema (nivel junior, limite de 50 palabras, codigo de apoyo acotado) y validacion del limite con un unico reintento correctivo dentro de `_draft_candidates()`.
- `agents/evaluator/app/service.py`: el prompt de sistema pide una justificacion de 50 palabras como maximo, y `evaluate_answer()` valida el limite con el mismo reintento unico.
- `agents/reviewer/app/service.py`: el prompt de sistema pide la version final en 50 palabras o menos (y acortar la propuesta si llegaba mas larga), y `review_justification()` valida el limite con el mismo reintento unico.
- `agents/{exercises,evaluator,reviewer}/app/agent_card.py`: las descripciones de las skills reflejan el nivel y el limite, que son parte del contrato que ve el orquestador.
- `agents/*/scripts/`: nuevos scripts de verificacion manual del limite (`verify_statement_limit.py` en ejercicios, `verify_justification_limit.py` en evaluador y revisor) para comprobarlo en vivo contra el modelo real.
- Sin cambios en `backend/`: ni `app/orchestrator.py` ni `app/answer_orchestrator.py` necesitan tocarse, porque cada agente garantiza su propia salida y los contratos A2A de entrada/salida no cambian. Tampoco cambian `frontend/`, `infra/supabase/migrations/` ni `docker-compose.yml`, y no hay ninguna columna ni restriccion nueva en base de datos.
- Efecto observable: los candidatos de las generaciones nuevas seran mas cortos y mas simples, y las respuestas evaluadas a partir de ahora traeran una justificacion breve; lo ya guardado se queda como esta.
