# Proposal

## Why

Hoy casi toda la politica de guardarrailes se decide en el proxy LiteLLM, que recibe el prompt ya montado como una cadena plana y **no puede distinguir que parte la escribio una persona y que parte la adjunto el sistema**. Esa ceguera es la causa comun de cuatro problemas, tres conocidos y uno nuevo:

- **Un fallo real y verificado:** los deployments de respaldo `evaluator-fallback-hf` y `reviewer-fallback-hf` no tienen guardarrailes vinculados, mientras `evaluator` y `reviewer` si llevan `presidio-pii`. Los guardarrailes se resuelven por deployment, y con `num_retries: 0` el fallback se dispara al primer fallo, asi que **cuando el modelo principal falla, el texto del alumno sale sin redactar hacia Hugging Face**. En `validator-fallback-hf` si estan vinculados, con comentario explicito: el patron se conocia y aqui se olvido.
- **Un hallazgo nuevo de privacidad:** Lakera y Presidio corren los dos en `pre_call`, y dentro del proxy los guardarrailes globales corren antes que los de deployment. Por eso el global `lakera-guard` enmascara la PII antes de que `presidio-pii-block` pueda verla, que es la razon de existir del `opted_out_global_guardrails`. La consecuencia en la ruta del evaluador es que **Lakera, un tercero de pago, recibe el texto del alumno sin redactar**, antes de que Presidio actue. Una propiedad de privacidad del sistema depende hoy del orden de ejecucion interno de una libreria de terceros: no esta bajo nuestro control, no esta cubierta por ningun test y puede cambiar en una actualizacion.
- **Falsos positivos que ya rompieron el producto:** `quitar-url-person-presidio` y `presidio-solo-evaluador-revisor` son dos changes dedicados a recortar el alcance de un control que tachaba contenido tecnico (`component.ts` -> `<PERSON>ponent.ts`). El recorte mitigo el sintoma; la causa sigue ahi, porque `IP_ADDRESS` y `CREDIT_CARD` pueden aparecer legitimamente en el codigo de apoyo que recibe el evaluador.
- **Un control sin consumidor:** `lakera-guard` corre en `monitor` sobre los cinco agentes, cuesta por llamada, anade latencia en el camino sincrono del alumno y no hay nadie que lea lo que registra.

La tesis del refactor: **el guardarrail es una propiedad del campo de texto, no del agente**. Una decision que necesita saber que campo es cada cosa pertenece a la capa del agente; una que no lo necesita pertenece al proxy.

## What Changes

**Capa de admision del agente (`input.py`)**

- El validador consulta el detector de PII en la admision y **rechaza**, en lugar de delegarlo al guardarrail de bloqueo del proxy. Complementa al regex existente sin solaparlo: el regex cubre DNI y NIE, que el detector no conoce; el detector cubre tarjeta e IP, que el regex no detecta (verificado ejecutando `find_pii_like` sobre ambos vectores).

**Capa de composicion del agente (`service.py`)**

- La redaccion de PII se aplica **al montar el prompt**, y **solo sobre los campos escritos por una persona**: la respuesta del alumno en el evaluador y en el revisor. El codigo de apoyo, los resumenes de web y los fragmentos de repositorio no se redactan nunca: no los escribe ningun usuario del sistema, redactarlos no protege a nadie y corrompe contenido tecnico.
- Como la redaccion ocurre antes de que el prompt salga del proceso, **todos** los destinatarios posteriores reciben el texto ya limpio: el detector de inyeccion, el proveedor, el proveedor de respaldo y las trazas.

**Capa del proxy (`infra/litellm/config.yaml`)**

- `presidio-pii` en modo MASK pasa a `default_on: true`: red de seguridad automatica y uniforme, gratis y autoalojada, para que **ningun deployment nuevo nazca sin proteccion**.
- `lakera-guard` deja de ser global. La deteccion de inyeccion se vincula en **modo bloqueo** a `evaluator`, `reviewer`, `validator` y sus tres deployments de respaldo: las entradas cuyo autor tiene incentivo adverso (el alumno) y el gate default-deny. **Se apaga en la ruta de generacion** (`generator` y su respaldo), que es donde solo produjo falsos positivos.
- **BREAKING (configuracion):** se eliminan los guardarrailes `lakera-guard` (global, `monitor`) y `presidio-pii-block`, y la metadata `opted_out_global_guardrails` de `infra/litellm/provision_keys.py`. De cuatro definiciones de guardarrail se pasa a dos, y de cuatro combinaciones distintas por deployment a una regla uniforme mas una excepcion.
- El `opted_out_global_guardrails` existia **unicamente** para deshacer el guardarrail global; sin global, no hay nada que deshacer.

**Verificacion e invariante**

- Comprobacion estatica nueva que parsea `infra/litellm/config.yaml` y verifica dos invariantes: todo deployment de fallback lleva al menos los guardarrailes de su primario (recorriendo `litellm_settings.fallbacks`), y existe una redaccion de PII activa de forma global que cubra cualquier deployment presente o futuro. No necesita red, modelo ni secretos, asi que **entra en el CI de GitHub Actions**, que hoy solo cubre `backend/**` y `frontend/**`.
- **BREAKING (verificacion):** se elimina `agents/validator/scripts/verify_guardrail_optout.py`, porque el mecanismo que verifica desaparece.
- La tasa de activacion de la red del proxy pasa a ser la **alarma del control de la capa de composicion**: con la redaccion en el agente funcionando no deberia saltar nunca, asi que si salta significa que un agente dejo de redactar un campo.

## Capabilities

### New Capabilities

Ninguna. El cambio reubica y simplifica comportamiento ya cubierto por capacidades existentes.

### Modified Capabilities

- `pii-redaction`: la redaccion pasa de aplicarse sobre el input completo en el proxy a aplicarse sobre el campo escrito por una persona en el agente, cubriendo asi a todo destinatario posterior y no solo al proveedor; el bloqueo de PII del validador pasa a la admision; y se anade la red de seguridad uniforme del proxy con su caracter de senal de anomalia.
- `prompt-injection-mitigation`: la deteccion automatizada deja de ser global y de solo observacion; pasa a bloquear en el evaluador, el revisor y el validador, y a no aplicarse en los agentes web, de codigo y de ejercicios. Los tres requisitos de delimitadores y frase defensiva no cambian.
- `technology-validation`: el pre-filtro determinista de la admision incorpora la consulta al detector de PII, y el requisito de guardarrailes de bloqueo del validador deja de cubrir la PII en el proxy (que se mueve a la admision) y mantiene el bloqueo de inyeccion.
- `agent-resilience`: se anade la invariante de que un deployment de fallback lleva al menos los guardarrailes de su primario, verificable de forma estatica.
- `litellm-agent-keys`: se elimina el requisito de exclusion del guardarrail global en la virtual key del validador.

## Impact

**Codigo**

- `agents/evaluator/app/`, `agents/reviewer/app/`: funcion de redaccion y su uso al montar el prompt.
- `agents/validator/app/input.py`: consulta al detector de PII en la admision.
- `agents/validator/scripts/verify_guardrail_optout.py`: se elimina.
- `infra/litellm/config.yaml`: de cuatro guardarrailes a dos y revinculacion por deployment.
- `infra/litellm/provision_keys.py`: se elimina `_AGENT_KEY_METADATA` y su reparacion.
- `docker-compose.yml`: `PRESIDIO_ANALYZER_API_BASE` y `PRESIDIO_ANONYMIZER_API_BASE` para los tres agentes que pasan a consultar Presidio, y dependencia de los servicios de Presidio. Ya comparten la red por defecto de Compose, asi que son alcanzables por nombre de servicio sin cambios de red.
- `.github/workflows/ci.yml`: el filtro por rutas incorpora la comprobacion estatica de la configuracion del proxy.

**Operacion**

- Tras desplegar hay que re-ejecutar `infra/litellm/provision_keys.py`: la metadata de exclusion deja de aplicarse. Las claves existentes siguen siendo validas; el script es idempotente.
- Se reduce el gasto y la latencia de Lakera en la ruta de generacion, donde deja de llamarse.

**Documentacion**

- `docs/especificacion-agentes.md` seccion 8 completa (los cuatro guardarrailes, el opt-out y la distincion MASK/BLOCK) y seccion 9.4.
- `docs/especificacion-backend.md` secciones 9.5 y 9.6.
- `capstone/juniortrainer-capstone.md`: la tabla de controles de 6.2, el apartado del opt-out, el mapeo OWASP de 6.3 (LLM01 y LLM02), el registro de riesgos de 6.4, el estado del red teaming de 6.5, la privacidad de 6.6, el inventario de verificadores de 5.4 y las lecciones de 7.

**Fuera de alcance**

- La politica de retencion de `answer.text` y de las trazas de Langfuse: es privacidad de persistencia, no de transito, y merece su propio change.
- Los umbrales y las alertas del cuadro de mando que consumirian la senal de la red del proxy.
- Los delimitadores y la frase defensiva de los siete prompts: ya estan en la capa correcta y no se tocan.
