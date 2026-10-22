# Design

## Context

Ver `proposal.md` seccion Why para la motivacion y los cuatro problemas que originan el cambio.

El estado de partida relevante para el diseno es el reparto de capas por las que pasa un texto antes de llegar a un proveedor de modelo, y lo que cada capa puede saber:

| Capa | Fichero | Sabe que campo es cada cosa | Cuesta dinero | Verificable sin stack |
|---|---|---|---|---|
| Admision | `agents/*/app/input.py` | Parcialmente | No | Si |
| Composicion | `agents/*/app/service.py` | **Si, del todo** | No | Si |
| Salida del proceso | `agents/*/app/llm.py` | No | No | Si |
| Proxy | `infra/litellm/config.yaml` | **No: cadena plana** | Si | No |

Hoy la redaccion de PII y la deteccion de inyeccion viven ambas en la capa del proxy, que es la unica ciega a la estructura del prompt y la unica cuyo orden interno de ejecucion no controlamos.

Restricciones que condicionan el diseno:

- Presidio ya corre autoalojado (`presidio-analyzer`, `presidio-anonymizer`) y es alcanzable por nombre de servicio: `docker-compose.yml` no declara redes, asi que todos los servicios comparten la red por defecto.
- El pre-filtro determinista del validador y Presidio son complementarios, no redundantes: el regex cubre DNI y NIE, que Presidio no reconoce; Presidio cubre tarjeta e IP, que el regex no detecta. Verificado ejecutando `find_pii_like` sobre ambos vectores.
- Los seis agentes son autocontenidos a proposito y no comparten libreria.

## Goals / Non-Goals

**Goals:**

- Que la accion de cada control se derive de la capa en la que vive, en lugar de ser un ajuste de configuracion por agente.
- Que ninguna propiedad de privacidad del sistema dependa del orden de ejecucion interno de una libreria de terceros.
- Que la cobertura de guardarrailes sea una invariante verificada, no una lista que hay que recordar mantener.
- Reducir la superficie de configuracion: de cuatro definiciones de guardarrail a dos, y de cuatro combinaciones por deployment a una regla uniforme mas una excepcion.

**Non-Goals:**

- Sustituir Presidio o Lakera por otra herramienta. Se usan las que ya hay.
- Extraer una libreria compartida entre agentes (ver decision 3).
- Redactar la salida del modelo. Sigue sin redactarse, por el requisito que ya existe en `pii-redaction`.

## Decisions

### Decision 1: la capa determina la accion, no la configuracion

En la admision solo se puede rechazar (no hay prompt que transformar todavia). En la composicion solo se puede transformar (ya se decidio admitir). Por tanto la eleccion entre "enmascarar" y "bloquear" deja de ser una politica que haya que elegir y configurar por agente: es una consecuencia de donde pertenece la decision.

Regla derivada: *si el campo no debe entrar, es admision y se rechaza; si debe entrar pero limpio, es composicion y se redacta.*

**Alternativa descartada:** mantener la politica por agente en la configuracion del proxy (estado actual). Se descarta porque obliga a tomar la decision en la capa con menos informacion disponible, que es el origen de los cuatro problemas de la propuesta.

### Decision 2: redactar el campo, no el prompt

La redaccion se aplica sobre el valor de `student_answer` antes de interpolarlo, no sobre el prompt montado.

**Alternativas descartadas:** (a) seguir redactando el prompt completo en el proxy, que es lo que produjo los falsos positivos que `quitar-url-person-presidio` y `presidio-solo-evaluador-revisor` intentaron parchear recortando entidades y agentes; (b) redactar el prompt completo pero desde el agente, que trasladaria el problema de sitio sin resolverlo. Solo la redaccion por campo elimina la causa.

### Decision 3: cada agente lleva su propia funcion de redaccion, duplicada

Los tres agentes afectados implementan su propia funcion de redaccion, sin libreria compartida.

Es coherente con la postura ya establecida y documentada del proyecto: el limite de 50 palabras esta duplicado a proposito entre evaluador y revisor (`valoracion-respuestas`, decision 7), y `service_auth.py`, `rate_limit.py`, `tracing.py` y `llm.py` son practicamente identicos en los seis agentes. Cada agente se despliega solo y no depende de nada mas.

**Alternativa descartada:** un paquete compartido. Se descarta por coherencia con esa postura y porque la funcion es pequena. El coste agregado de esa duplicacion es real y esta reconocido como deuda a revisar de forma global, pero hacerlo aqui mezclaria dos cambios.

### Decision 4: los agentes consultan a Presidio por HTTP, no con su SDK

Los agentes llaman a los servicios `presidio-analyzer` y `presidio-anonymizer` que ya estan levantados, igual que hace hoy el proxy.

**Alternativa descartada:** incorporar el SDK de Python de Presidio a cada agente. Se descarta porque arrastra una dependencia pesada (modelos de spaCy) a tres imagenes y duplica lo que un servicio ya en marcha hace.

### Decision 5: la redaccion del agente es fail-closed

Si Presidio no responde, la tarea falla en lugar de enviar el texto sin redactar.

No es un cambio de postura: hoy la integracion de Presidio en LiteLLM ya es fail-closed con `pii_entities_config` poblado. Mantenerla es lo coherente, y lo contrario convertiria una caida de un servicio local en una fuga silenciosa.

**Alternativa descartada:** fail-open con registro de advertencia, como se hace con la memoria de los agentes. Se descarta porque la politica de "una memoria caida no bloquea la generacion" aplica a una optimizacion, no a un control de privacidad.

### Decision 6: la deteccion de inyeccion se mantiene en el validador, en bloqueo

El validador conserva la deteccion de inyeccion en modo bloqueo sobre su deployment principal y el de respaldo.

El mecanismo de exclusion del guardarrail global desaparece igualmente, porque estaba atado al caracter *global* del guardarrail, no al del validador. Mantener el bloqueo en el validador cuesta una linea de configuracion y preserva la defensa de un gate default-deny.

**Alternativa descartada:** apagarlo tambien en el validador, aplicando de forma estricta el criterio de "bloquear solo donde el autor tiene incentivo adverso". Se descarta porque el ahorro es una linea y la perdida es una capa de defensa en el unico punto del sistema cuyo proposito entero es denegar por defecto.

### Decision 7: la deteccion de inyeccion se apaga en la ruta de generacion

Los agentes web, de codigo y de ejercicios dejan de pasar por el detector.

Motivos: las unicas detecciones observadas ahi fueron falsos positivos sobre rutas de repositorio (`fix-falso-positivo-lakera`); el modo de solo observacion no tiene ningun consumidor de la senal; y cuesta una llamada de pago y latencia en `pre_call` por cada llamada de tres agentes.

**Alternativa descartada:** mantener la observacion y anadir un consumidor de la senal (alerta o cuadro de mando). Se descarta de momento porque supondria seguir pagando una senal antes de saber si merece consumirse. Si la medicion posterior muestra valor, se vuelve a vincular por deployment en una linea.

### Decision 8: la red del proxy se activa de forma global y su activacion es una senal

`presidio-pii` pasa a `default_on: true`, de modo que cualquier deployment, presente o futuro, nace con redaccion de PII sin que nadie tenga que acordarse de vincularla.

El reparto resultante es explicable en una frase: **automatico para el control gratuito y autoalojado, explicito para el de pago y externo.** Y tiene un efecto util: con la decision 2 operativa, esa red no deberia sustituir nada nunca, asi que su tasa de activacion se convierte en el detector de fallos de la redaccion del agente.

### Decision 9: un bloqueo del detector en el evaluador falla la evaluacion

Un bloqueo es un fallo de la llamada, asi que sigue el comportamiento ya especificado en `answer-evaluation`: se responde `502` y no se persiste nada. El alumno puede reenviar su respuesta.

La consecuencia es que un falso positivo sobre una respuesta legitima impide corregir a ese alumno. Es el riesgo principal del cambio y se trata en la seccion siguiente.

### Decision 10: la redaccion pide entidades explicitas y completa lo que el detector no cubre

Dos detalles que solo aparecieron al sondear el detector antes de programar contra el, y que condicionan la implementacion:

**Entidades explicitas.** La llamada al detector enumera las cinco entidades de la politica vigente. Con el conjunto por defecto, `src/app/core/role.guard.ts` dispara `PERSON` y `URL` -- comprobado--, que son precisamente las dos entidades que `quitar-url-person-presidio` retiro. Con la lista explicita, ese mismo texto no dispara nada. Delegar en el conjunto por defecto reintroduciria el fallo que dos changes anteriores se dedicaron a quitar.

**Telefono nacional.** `PHONE_NUMBER` no reconoce un numero espanol sin prefijo internacional: `600123456` no se detecta, `+34 600 123 456` si. La causa es que la imagen por defecto del analizador solo trae reconocedores en ingles (una llamada con `language: es` responde `500 No matching recognizers were found`), asi que el reconocedor de telefono asume regiones estadounidenses. Para las otras cuatro entidades es inocuo, porque son expresion regular y digito de control y no dependen del idioma.

La redaccion del agente anade por tanto una comprobacion determinista del telefono espanol, en la linea del pre-filtro que el validador ya tiene para el DNI -- que existe por el mismo motivo: cubrir de forma no probabilistica lo que el detector no conoce. Es alcance anadido sobre la propuesta inicial, aprobado expresamente, y cierra un hueco **anterior** a este change: hoy la capacidad afirma redactar el telefono y un movil espanol escrito como se escribe no se redacta nunca.

**IBAN en prosa.** Al verificar la implementacion aparecio un segundo caso de la misma forma: el reconocedor de IBAN detecta `ES91...1332` suelto, al final de una frase o seguido de un signo de puntuacion, pero NO cuando le sigue mas texto (`... desde 2019`). A diferencia del telefono, el IBAN si figura en la politica de entidades vigente, asi que cubrirlo no es alcance anadido: es lo que hace que el requisito ya existente se cumpla de verdad. Se usa el mismo patron que el pre-filtro del validador ya aplica en produccion.

**Alternativas descartadas:** (a) configurar el analizador con la region espanola, que exige anadir modelos de idioma a la imagen y convierte una deteccion determinista en una probabilistica dependiente del idioma; (b) aceptar el hueco y documentarlo, que deja sin cubrir el campo mas sensible del sistema por el coste de una expresion regular.

El patron exige nueve digitos que empiecen por `6`, `7`, `8` o `9` -- los digitos iniciales validos en Espana-- con separadores opcionales y sin digitos pegados a los extremos. Acotarlo asi evita marcar cualquier cifra larga que aparezca en la prosa de un alumno. El codigo de apoyo no se redacta nunca (decision 2), asi que una constante numerica del codigo no se ve afectada.

## Risks / Trade-offs

**Falso positivo del detector de inyeccion sobre una respuesta legitima de un alumno** → **MEDIDO, y la hipotesis era falsa.** Sobre el corpus de 15 respuestas reales ya almacenadas, con el texto redactado -- que es lo que el detector vera en produccion--, **1 de 15 se marca** como `prompt_attack`. La respuesta marcada son 11 palabras, sin un solo termino tipico de inyeccion, con veredicto `incomplete`: un falso positivo inequivoco. Y el propio detector la clasifica como `l4_less_likely`, es decir *poco probable*, pero la politica por defecto de Lakera la bloquea igualmente (`action: enforce`).

Consecuencia para la decision 9: **el bloqueo NO se activa en el evaluador ni en el revisor.** Con esa tasa, activarlo impediria corregir a aproximadamente una respuesta de cada quince, y el falso positivo que motivo `fix-falso-positivo-lakera` resulta no ser un caso aislado del dominio de las rutas de repositorio: tambien ocurre sobre prosa de alumno.

El camino para activarlo existe y es concreto: la politica de Lakera se gestiona en su plataforma, no en este repositorio, y el umbral de enforcement se puede subir para que solo bloquee en niveles de confianza altos. Ajustarlo y volver a medir sobre el mismo corpus es la condicion previa, y es trabajo de otro change.

**Apagar el detector en la ruta de generacion deja sin deteccion automatizada el contenido de repositorio y de web** → Los delimitadores y la frase defensiva siguen aplicandose, y ningun agente tiene herramientas de escritura: el radio de dano de una inyeccion que burle esa capa queda acotado a la calidad del resultado, que un humano revisa antes de guardar.

**Una caida de Presidio detiene las evaluaciones** → Es la postura actual (decision 5), el servicio es local y tiene healthcheck, y la red del proxy sigue en pie.

**Deriva entre las tres implementaciones duplicadas de la redaccion** → Cada agente lleva su test unitario con los mismos vectores, incluidos los dos que atraviesan el pre-filtro (tarjeta e IP).

**El cambio elimina un requisito y un verificador anadidos muy recientemente** → Sin mitigacion: es el coste de haber llegado a este diseno por ese camino. Queda registrado en la propuesta y en el delta de `litellm-agent-keys`.

**Re-ejecutar el aprovisionamiento de virtual keys es un paso manual de despliegue** → El script es idempotente y las keys existentes siguen siendo validas; la metadata que quede es inerte.

## Migration Plan

Por fases, cada una desplegable y reversible por separado. El orden no es arbitrario: la fase 4 no puede entrar antes de la 2 y la 3, o el sistema queda sin redaccion en medio.

1. **Tapar el fallo, sin cambio de comportamiento.** Vincular la redaccion a los dos deployments de respaldo descubiertos. Rollback: revertir dos lineas.
2. **La invariante en CI.** Comprobacion estatica de la configuracion del proxy, incorporada al workflow. No afecta a runtime.
3. **Redaccion en el agente.** Variables de Presidio y dependencia de servicio en Compose para los tres agentes, funcion de redaccion con su test, y uso en la composicion del prompt. En este punto la redaccion se aplica dos veces (agente y proxy), que es inocuo y deliberado: deja el sistema protegido durante la transicion.
4. **Admision del validador.** Consulta a Presidio en `input.py`.
5. **Simplificar el proxy.** Eliminar el guardarrail global de inyeccion y el de bloqueo de PII, pasar la red a global, vincular la deteccion de inyeccion a los deployments que la necesitan, y eliminar la metadata de exclusion y su verificador. Re-ejecutar el aprovisionamiento de keys.
6. **Medir.** Tasa de activacion de la red del proxy (debe ser cero: si no, la fase 3 esta incompleta en algun campo) y tasa de falsos positivos del detector donde bloquea.

Rollback global: la configuracion del proxy y el aprovisionamiento de keys vuelven al estado anterior con un revert; la redaccion en el agente puede quedarse sin dano, porque redactar dos veces es inocuo.

## Open Questions

- El formato exacto del marcador que aplica Presidio al anonimizar desde el agente (si coincide con el `<TIPO>` que hoy produce la integracion de LiteLLM o hay que fijarlo explicitamente en la llamada al anonimizador). Se resuelve al implementar; no afecta a los requisitos, al enfoque ni al desglose de tareas.
