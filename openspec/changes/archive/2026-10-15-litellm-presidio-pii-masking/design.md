# Design

## Context

Ver `proposal.md` para la motivacion. Investigacion hecha contra documentacion oficial (no supuesta):

- LiteLLM soporta Presidio como guardrail nativo (`guardrail: presidio` en `config.yaml`), pero a diferencia de Lakera **no es un servicio SaaS**: necesita dos contenedores propios, `presidio-analyzer` (detecta entidades) y `presidio-anonymizer` (las sustituye), imagenes oficiales `mcr.microsoft.com/presidio-analyzer` / `mcr.microsoft.com/presidio-anonymizer`, puerto interno `3000` en ambas.
- Configuracion: `PRESIDIO_ANALYZER_API_BASE` y `PRESIDIO_ANONYMIZER_API_BASE` apuntando a esos dos servicios; `pii_entities_config` decide, entidad por entidad, si se enmascara (`MASK`, sustituye por un marcador) o se bloquea la llamada entera (`BLOCK`).
- Mismo mecanismo `default_on: true` que ya usa el guardrail de Lakera: se aplica a toda llamada sin que el agente la pida explicitamente.
- El modelo de idioma de `presidio-analyzer` es ingles por defecto. Decision ya tomada con el usuario: usar la imagen oficial tal cual, aceptando que la deteccion de `PERSON` (nombres) en español tendra peor recall que con un modelo en español -- los patrones por regex (email, telefono, tarjeta, IP, IBAN, URL) no dependen del idioma y no se ven afectados.

## Goals / Non-Goals

**Goals:**
- Redactar PII real antes de que salga hacia el proveedor, en los 5 agentes, sin cambios de codigo.
- Reusar el mismo patron que `litellm-lakera-guardrail`: `default_on`, sin tocar `agents/*`.

**Non-Goals:**
- No se instala un modelo de idioma en español en esta propuesta (decision explicita, ver proposal.md). Si el recall de `PERSON` en español resulta insuficiente en uso real, seria una propuesta aparte: construir una imagen propia de `presidio-analyzer` con `es_core_news_lg`.
- No se usa `BLOCK` para ninguna entidad: el objetivo es redactar, no rechazar la llamada -- a diferencia de Lakera (donde bloquear tiene sentido porque es un ataque), aqui el dato personal no es malicioso, solo no deberia salir de la infraestructura tal cual.
- No se decide aqui si redactar tambien el output del modelo (`mode: post_call` ademas de `pre_call`): el enfoque de esta propuesta es el input (lo que el alumno escribe), que es el canal real de fuga de datos personales reales; el output del modelo es contenido generado por el LLM, no texto literal de un alumno, con un perfil de riesgo distinto.
- No se gestiona el coste/recursos de los contenedores de Presidio como una propuesta de infraestructura aparte: son dos servicios mas en `docker-compose.yml`, mismo patron que `litellm-db`.

## Decisions

- **Dos contenedores dedicados, imagenes oficiales de Microsoft, sin puerto publicado al host.** Mismo patron que los 5 agentes (`expose`, no `ports`): solo `litellm` necesita alcanzarlos, no hace falta exponerlos fuera de la red interna de docker-compose.
- **`pii_entities_config` solo con entidades universales + `PERSON`, no el catalogo completo de Presidio.** Presidio detecta por defecto mas entidades de las relevantes aqui (p. ej. matriculas de EEUU, licencias medicas, `US_SSN`). Se acota a las que tienen sentido en este contexto: `EMAIL_ADDRESS`, `PHONE_NUMBER`, `CREDIT_CARD`, `IP_ADDRESS`, `IBAN_CODE`, `URL`, `PERSON`. Menos ruido, mas facil de razonar sobre que se esta redactando y por que.
- **Mismo mecanismo `default_on`/`mode: pre_call` que Lakera, como un guardrail mas en la misma lista.** No hay necesidad de un mecanismo distinto: LiteLLM ya soporta varios guardrails en la misma `config.yaml`, cada uno corriendo en su propio paso.
- **Pin de version de las imagenes de Presidio, no `:latest`.** Ya se vio con `litellm:main-latest` que una tag flotante puede introducir un crash inesperado sin ningun cambio de nuestra parte (ver `litellm-lakera-guardrail`, hallazgo del SIGSEGV). Las tareas de implementacion deben fijar una version concreta de `presidio-analyzer`/`presidio-anonymizer` (la ultima estable disponible en el momento de implementar), no `:latest`.

## Risks / Trade-offs

- [Nombres de persona en español detectados con peor recall que con un modelo en español -- un nombre real podria no detectarse y llegar sin redactar al proveedor] → Mitigacion: aceptado explicitamente por el usuario para esta primera iteracion; los patrones por regex (email, telefono, etc., probablemente el dato mas sensible en la practica) no se ven afectados. Si el recall de `PERSON` resulta insuficiente, es una propuesta aparte con una imagen de Presidio en español.
- [Dos contenedores mas que mantener, con su propio ciclo de arranque -- si `presidio-analyzer`/`presidio-anonymizer` no responden, el guardrail `pre_call` podria bloquear toda llamada (mismo patron de fail-closed que Lakera, no investigado aun para Presidio especificamente)] → Mitigacion: se verifica explicitamente en las tareas de implementacion (igual que se hizo para Lakera: auth invalida, conexion rechazada, host inalcanzable), no se asume el mismo comportamiento solo porque el framework es el mismo.
- [`BLOCK` no se usa, asi que una llamada con PII sigue completandose (redactada) en vez de rechazarse -- si algun dato personal escapara a la deteccion de Presidio, llegaria al proveedor sin ningun aviso] → Mitigacion: es el trade-off explicito de "redactar, no bloquear" que pide esta propuesta; no se puede bloquear contenido legitimo de alumnos solo porque mencione un email sin que eso sea un problema de seguridad en si mismo.
