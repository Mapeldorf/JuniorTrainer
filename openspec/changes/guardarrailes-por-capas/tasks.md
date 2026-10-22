# Tasks

## 1. Invariante de cobertura, verificada estaticamente

- [x] 1.1 Crear `infra/litellm/verify_guardrail_coverage.py`, que parsea `infra/litellm/config.yaml` y comprueba dos invariantes: todo deployment de fallback lleva al menos los guardarrailes de su primario (recorriendo `litellm_settings.fallbacks`) y existe al menos un guardarrail de redaccion de PII con `default_on: true`. Verificar: ejecutado contra la configuracion ACTUAL debe **fallar**, nombrando `evaluator-fallback-hf` y `reviewer-fallback-hf` como descubiertos y la ausencia de red global -- es decir, reproduce el fallo de la propuesta antes de arreglarlo.
- [x] 1.2 Anadir al script sus propios casos de prueba con configuraciones sinteticas: coherente, fallback descubierto y sin red global. Verificar: los tres casos dan el resultado esperado sin tocar la configuracion real.
- [x] 1.3 Incorporar la comprobacion al workflow de CI con filtro de rutas sobre `infra/litellm/**`. Verificar: un PR que toque ese directorio ejecuta el nuevo trabajo, y uno que no lo toque lo omite.

## 2. Cobertura de los deployments de respaldo

- [x] 2.1 Vincular `presidio-pii` a `evaluator-fallback-hf` y `reviewer-fallback-hf` en `infra/litellm/config.yaml`. Verificar: `infra/litellm/verify_guardrail_coverage.py` deja de senalar esos dos deployments (la invariante de red global seguira fallando hasta la tarea 5.1).
- [ ] 2.2 Comprobar en vivo que el respaldo redacta: con el stack levantado y forzando el fallo del modelo principal del evaluador, una respuesta con un email llega redactada al proveedor de respaldo. Verificar: la llamada se completa y la traza no contiene el email.

## 3. Redaccion en la capa de composicion

- [x] 3.1 Pasar `PRESIDIO_ANALYZER_API_BASE` y `PRESIDIO_ANONYMIZER_API_BASE` a `agent-evaluator`, `agent-reviewer` y `agent-validator` en `docker-compose.yml`, con `depends_on` de los dos servicios de Presidio. Verificar: desde el contenedor de cada uno de los tres agentes, una peticion al analizador responde.
- [x] 3.2 Implementar la funcion de redaccion en `agents/evaluator/app/`, que consulta al analizador y al anonimizador **solicitando la lista explicita de las cinco entidades** (design.md decision 10) y es fail-closed si no responden (decision 5). Verificar: test unitario con los cinco tipos de entidad y un caso de servicio caido que debe propagar el fallo en vez de devolver el texto original.
- [x] 3.3 Anadir a esa funcion las comprobaciones deterministas de lo que el detector no cubre en prosa: el telefono espanol sin prefijo internacional (alcance ampliado) y el IBAN que no esta al final de la frase (requisito ya vigente que no se cumplia). Verificar: test con `600123456`, con separadores (`600 12 34 56`, `600-123-456`), con prefijo (`+34 600 123 456`) y con cifras que NO son telefono (ocho digitos, y nueve que empiezan por un digito no valido) que deben quedar intactas, y con un IBAN en medio de una frase.
- [x] 3.4 Aplicar la redaccion unicamente a `student_answer` al montar el prompt del evaluador, nunca a `statement`, `code` ni `expected_answer` (design.md decision 2). Verificar: test que comprueba que una respuesta con un email sale redactada y que un bloque de codigo de apoyo que contiene `127.0.0.1` sale intacto.
- [x] 3.5 Replicar 3.2, 3.3 y 3.4 en `agents/reviewer/app/`, aplicando la redaccion solo a `student_answer` (la `justification` recibida la genera un modelo, no una persona). Verificar: los mismos tests, con los mismos vectores, en el revisor.
- [ ] 3.6 Comprobacion manual de extremo a extremo: responder un ejercicio con un email real en el texto. Verificar: el veredicto se emite con normalidad y ni el proveedor ni la traza reciben el email.
- [x] 3.7 Actualizar en `capstone/juniortrainer-capstone.md` la seccion 6.6 (donde se aplica la redaccion, a que campos, y el hueco del telefono nacional que se cierra) y la tabla de controles de 6.2 en lo relativo a Presidio. Verificar: no queda ninguna afirmacion de que la redaccion se aplique al prompt completo en el proxy.

## 4. Admision del validador

- [x] 4.1 Consultar a Presidio en `agents/validator/app/input.py` y rechazar la peticion si detecta PII, antes de invocar al modelo, manteniendo el pre-filtro de regex existente. Verificar: test que confirma rechazo con un numero de tarjeta y con una IP (los dos vectores que atraviesan el regex) y aceptacion con tecnologias reales.
- [x] 4.2 Ampliar `agents/validator/scripts/verify_validator.py` con el rechazo en admision por PII. Verificar: el script pasa con el stack levantado.

## 5. Simplificacion del proxy

- [x] 5.1 En `infra/litellm/config.yaml`: pasar `presidio-pii` a `default_on: true`, eliminar el guardarrail global `lakera-guard` y el de bloqueo `presidio-pii-block`, dejar `lakera-guard-block` vinculado solo al deployment `validator` y a `validator-fallback-hf`, y corregir su comentario, que afirma una doble llamada a Lakera que el opt-out ya habia eliminado. Verificar: `verify_guardrail_coverage.py` pasa por completo, y `docker compose up litellm` arranca sin error de configuracion.
- [x] 5.2 Eliminar `_AGENT_KEY_METADATA` y su reparacion en `_missing_fields` de `infra/litellm/provision_keys.py`. Verificar: re-ejecutar el script sobre las keys existentes no las modifica ni vuelve a aplicar la metadata, y las seis siguen funcionando.
- [x] 5.3 Eliminar `agents/validator/scripts/verify_guardrail_optout.py`. Verificar: no queda ninguna referencia a el en el repositorio.
- [x] 5.4 Comprobar que la red del proxy no interfiere: con la redaccion del agente operativa, una evaluacion con PII en la respuesta se completa y la red de Presidio del proxy no sustituye nada. Verificar: la traza muestra el texto ya redactado por el agente.
- [x] 5.5 Actualizar en `capstone/juniortrainer-capstone.md` el inventario de controles de 6.2 (de cuatro guardarrailes a dos, sin el apartado del opt-out), el mapeo OWASP de 6.3 en LLM01 y LLM02, el registro de riesgos de 6.4 y el inventario de verificadores de 5.4. Verificar: ninguna seccion menciona el guardarrail global ni `opted_out_global_guardrails`.
- [ ] 5.6 Actualizar `docs/especificacion-agentes.md` seccion 8 completa y 9.4, y `docs/especificacion-backend.md` 9.5 y 9.6 (ficheros locales, `docs/` esta en `.gitignore`). Verificar: coherencia con la configuracion resultante.

## 6. Deteccion de inyeccion donde bloquea

- [x] 6.1 Medir la tasa de falsos positivos del detector de inyeccion sobre un corpus de respuestas reales ya almacenadas en `answer`, en modo de solo observacion. Verificar: informe con el numero de respuestas evaluadas y cuantas se marcarian. **RESULTADO: 1 de 15 marcada** (`prompt_attack`, `l4_less_likely`), sobre una respuesta de 11 palabras sin terminos de inyeccion y con veredicto `incomplete`: falso positivo inequivoco.
- [x] 6.2 Si la tasa de 6.1 es cero, vincular `lakera-guard-block` a `evaluator`, `reviewer`, `evaluator-fallback-hf` y `reviewer-fallback-hf`. Si no es cero, no activar el bloqueo y registrar el resultado como hallazgo que obliga a revisar la decision 9 del diseno antes de continuar. **RAMA NEGATIVA: no se activa.** La tasa es 1/15, no cero. Registrado en design.md (decision 9, seccion de riesgos) y en el documento (6.5). Condicion previa para activarlo: subir el umbral de enforcement en la plataforma de Lakera y volver a medir sobre el mismo corpus, en otro change.
- [ ] 6.3 Medir la tasa de activacion de la red de redaccion del proxy tras una tanda de evaluaciones reales. Verificar: es cero; cualquier activacion identifica un campo que el grupo 3 dejo sin redactar.
- [x] 6.4 Actualizar en `capstone/juniortrainer-capstone.md` la seccion 6.5 con el resultado de 6.1 y el estado del hueco de verificacion, y 5.5 con las dos metricas nuevas. Verificar: la seccion refleja numeros medidos, no intenciones.

## Workflow follow-up

- Archivar el change con `/opsx:archive` para sincronizar los cinco deltas con `openspec/specs/`.
- Tras el archivado, comprobar que `openspec validate --all` sigue pasando y que `litellm-agent-keys` ya no contiene el requisito eliminado.
