# Spec Delta

## ADDED Requirements

### Requirement: Bloqueo automatizado de prompt injection donde el autor tiene incentivo adverso
El sistema SHALL ejecutar una comprobacion automatizada de prompt injection sobre el input de toda llamada de los agentes evaluador, revisor y validador al proxy, tanto hacia su modelo principal como hacia su modelo de respaldo, antes de invocar al proveedor subyacente, y SHALL rechazar la llamada cuando detecte un intento.

#### Scenario: Input sin intento de prompt injection
- **WHEN** el evaluador, el revisor o el validador envia una llamada cuyo input no contiene ningun intento de prompt injection
- **THEN** la comprobacion lo deja pasar y la llamada al proveedor subyacente se realiza con normalidad

#### Scenario: Intento de prompt injection en la respuesta de un alumno
- **WHEN** el input de una llamada del evaluador o del revisor contiene un intento de prompt injection que el detector reconoce
- **THEN** la comprobacion SHALL bloquear la llamada, la evaluacion falla y no se persiste ninguna respuesta

#### Scenario: Intento de prompt injection en el validador
- **WHEN** el input de una llamada del agente validador contiene un intento de prompt injection que el detector reconoce
- **THEN** la comprobacion SHALL bloquear la llamada y la generacion queda en estado de error

#### Scenario: La comprobacion cubre tambien el modelo de respaldo
- **WHEN** la llamada de uno de esos agentes se dirige a su modelo de respaldo tras un fallo del principal
- **THEN** la comprobacion se aplica igualmente antes de invocar al proveedor de respaldo

### Requirement: La ruta de generacion no pasa por la comprobacion automatizada
El sistema SHALL NOT ejecutar la comprobacion automatizada de prompt injection sobre las llamadas de los agentes web, de codigo y de ejercicios, cuyo contenido de entrada procede de terceros o de un repositorio y no de un autor con incentivo para manipular al modelo.

#### Scenario: Contenido benigno de repositorio
- **WHEN** el agente de codigo procesa contenido que un detector de prompt injection marcaria como falso positivo (p. ej. una ruta o un nombre de fichero que contiene la palabra "role")
- **THEN** ese contenido no pasa por la comprobacion automatizada y la tarea del agente continua con normalidad, sin que un falso positivo pueda interrumpirla

#### Scenario: Un intento de inyeccion desde un repositorio o una pagina web
- **WHEN** el contenido de un repositorio o de un resultado de busqueda contiene un intento de manipular al modelo
- **THEN** la mitigacion aplicable es la delimitacion de ese contenido como dato y la ausencia de herramientas de escritura en el agente, que acotan el efecto a la calidad del resultado

## REMOVED Requirements

### Requirement: Deteccion automatizada de prompt injection en el proxy
**Reason**: El requisito definia la comprobacion como global sobre los seis agentes y de solo observacion para cinco de ellos. Ese diseno tenia tres problemas: la observacion no bloquea nada y no tenia ningun consumidor de la senal, de modo que no actuaba como control; al ser global se ejecutaba antes de los guardarrailes de deployment y enmascaraba la PII antes de que el guardarrail de bloqueo pudiera verla, lo que obligo a introducir un mecanismo de exclusion en la virtual key del validador; y se aplicaba a la ruta de generacion, donde las unicas detecciones observadas fueron falsos positivos sobre rutas de repositorio. Lo sustituyen dos requisitos que separan ambos casos: bloqueo efectivo donde el autor del texto tiene incentivo adverso, y ausencia de comprobacion en la ruta de generacion.

**Migration**: Al dejar de ser global, desaparece la necesidad del mecanismo de exclusion (ver el delta de `litellm-agent-keys`). Hay que re-ejecutar `infra/litellm/provision_keys.py` tras desplegar la configuracion. Los tres requisitos de delimitacion de contenido no confiable como dato no cambian y siguen siendo la mitigacion de base en los seis agentes.
