# Spec Delta

## ADDED Requirements

### Requirement: Redaccion acotada a los campos escritos por una persona
El sistema SHALL aplicar la redaccion de PII unicamente a los campos de una llamada escritos por una persona -- la respuesta del alumno en el evaluador y en el revisor -- y SHALL NOT aplicarla al resto del contenido de esa misma llamada, que el sistema deriva de otras fuentes.

#### Scenario: Solo se redacta el campo escrito por la persona
- **WHEN** una llamada del evaluador lleva una respuesta de alumno con un dato personal y, en el mismo prompt, codigo de apoyo
- **THEN** el sistema SHALL redactar el dato de la respuesta del alumno y SHALL NOT alterar el codigo de apoyo

#### Scenario: Contenido tecnico que parece un dato personal
- **WHEN** el enunciado, el codigo de apoyo, la respuesta esperada, un resumen de documentacion o un fragmento de repositorio contiene una direccion IP, una cadena larga de digitos o una ruta de fichero detectable como entidad
- **THEN** el sistema SHALL entregarlo al modelo tal cual, sin sustituir nada por un marcador

#### Scenario: Llamada sin texto escrito por una persona
- **WHEN** el agente web, el de codigo o el de ejercicios realiza una llamada
- **THEN** ningun campo de esa llamada se redacta en el agente: su contenido no lo escribe ningun usuario del sistema

### Requirement: Red de seguridad de redaccion en el proxy
El sistema SHALL aplicar la redaccion de PII, en modo de sustitucion por marcador, a las llamadas de todos los deployments del proxy de forma automatica, incluidos los que se anadan en el futuro, como red de seguridad independiente de la redaccion que aplica el agente.

#### Scenario: Un deployment nuevo nace protegido
- **WHEN** se anade un deployment nuevo a la configuracion del proxy sin declarar explicitamente ningun guardarrail de PII
- **THEN** la redaccion de PII se aplica igualmente a sus llamadas, sin necesidad de vincularla a mano

#### Scenario: La red actua si el agente no redacto
- **WHEN** una llamada llega al proxy con un dato personal que el agente no redacto
- **THEN** el sistema SHALL sustituirlo por su marcador generico antes de invocar al proveedor subyacente

### Requirement: La activacion de la red de seguridad es una senal de anomalia
El sistema SHALL registrar como anomalia cada activacion de la red de seguridad de redaccion del proxy: con la redaccion del agente operativa esa red no deberia sustituir nada, asi que una activacion indica que algun agente dejo de redactar un campo escrito por una persona.

#### Scenario: La red del proxy sustituye un dato
- **WHEN** la red de seguridad del proxy sustituye un dato personal por su marcador
- **THEN** el sistema SHALL registrar esa activacion como anomalia, distinguible de una redaccion normal del agente

#### Scenario: Operacion normal
- **WHEN** la redaccion del agente funciona correctamente sobre todos los campos escritos por una persona
- **THEN** la red de seguridad del proxy no sustituye nada y no se registra ninguna anomalia

## MODIFIED Requirements

### Requirement: Redaccion automatica de PII antes de la llamada al proveedor
El sistema SHALL detectar y sustituir por un marcador generico cualquier email, telefono, numero de tarjeta, direccion IP o codigo IBAN escrito por una persona en el contenido de una llamada del agente evaluador o del agente revisor, **antes de que ese contenido salga del proceso del agente**, de forma que ningun destinatario posterior lo reciba en claro: ni el detector automatizado de prompt injection, ni el proveedor del modelo, ni el proveedor de respaldo, ni las trazas.

#### Scenario: Input sin datos personales
- **WHEN** el evaluador o el revisor envia una llamada cuyo input no contiene ningun dato personal detectable
- **THEN** la llamada llega al proveedor sin modificar

#### Scenario: Input con un email o telefono real
- **WHEN** el input de una llamada del evaluador o del revisor contiene un email o un numero de telefono real
- **THEN** el sistema SHALL sustituirlo por su marcador generico correspondiente antes de que la llamada salga del proceso del agente

#### Scenario: Ningun destinatario posterior recibe el dato en claro
- **WHEN** la respuesta de un alumno contiene un dato personal y la llamada del evaluador recorre el detector de prompt injection y, tras un fallo del modelo principal, el proveedor de respaldo
- **THEN** tanto el detector como el proveedor principal, el de respaldo y las trazas reciben el contenido ya redactado

### Requirement: Deteccion de PII en modo de bloqueo en el validador
El agente validador SHALL ejecutar la deteccion de PII en la admision de la peticion, antes de invocar al modelo, y SHALL rechazar la peticion cuando detecte un email, telefono, numero de tarjeta, direccion IP o codigo IBAN, en lugar de sustituirlo por un marcador y continuar.

#### Scenario: Input del validador con un dato personal
- **WHEN** una de las tecnologias de la peticion contiene un dato personal detectable (email, telefono, tarjeta, IP o IBAN)
- **THEN** el validador rechaza la peticion en la admision y la generacion queda en estado de error, sin que el modelo llegue a ser invocado

#### Scenario: Input del validador sin datos personales
- **WHEN** ninguna de las tecnologias de la peticion contiene un dato personal detectable
- **THEN** la admision no rechaza y la validacion continua con el modelo

#### Scenario: Los demas agentes no se ven afectados
- **WHEN** el agente evaluador o el agente revisor procesan una llamada
- **THEN** la redaccion sigue sustituyendo el dato por su marcador y continuando (no bloquea), y los agentes web, de codigo y de ejercicios siguen sin redactar nada en el agente

## REMOVED Requirements

### Requirement: Redaccion aplicada automaticamente a las llamadas con texto del alumno
**Reason**: El requisito definia la redaccion como algo que ocurria en el proxy sobre el input completo de la llamada, "sin que ningun agente tenga que solicitarla explicitamente ni requiera cambios en su codigo". Ese automatismo es precisamente lo que impedia distinguir el campo escrito por una persona del contenido que el sistema deriva de otras fuentes, y lo que obligo a recortar entidades (`quitar-url-person-presidio`) y agentes (`presidio-solo-evaluador-revisor`) para contener los falsos positivos sobre contenido tecnico. Lo sustituye el requisito "Redaccion acotada a los campos escritos por una persona", que fija la redaccion por campo en el agente, mas la red de seguridad del proxy, que conserva el caracter automatico para cualquier deployment presente o futuro.

**Migration**: No hay migracion de datos. La cobertura no se reduce en ningun momento de la transicion: la red de seguridad del proxy se activa de forma global antes de retirar nada, de modo que el sistema queda redactando dos veces (agente y proxy) durante el despliegue, que es inocuo y deliberado.
