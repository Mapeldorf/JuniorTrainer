# llm-provider-routing Specification

## Purpose
Define que proveedores de inferencia pueden recibir el trafico de los modelos logicos que sirve un agregador (OpenRouter), con que garantias de retencion y de jurisdiccion, como falla una politica que no puede cumplirse y como se verifica de forma estatica.

## Requirements

### Requirement: Politica de enrutado en todo deployment servido por un agregador
Todo deployment del proxy cuyo modelo lo sirve OpenRouter SHALL enviar a OpenRouter una politica de enrutado que exija a la vez: que el proveedor no recolecte los datos de la peticion, que tenga retencion cero (ZDR), y que pertenezca a una lista cerrada de proveedores permitidos. La politica SHALL ser la misma para todos esos deployments.

#### Scenario: Llamada de un agente con la politica activa
- **WHEN** un agente llama a su modelo logico y el proxy la envia a OpenRouter
- **THEN** OpenRouter solo puede asignarla a un proveedor que cumpla las tres restricciones a la vez

#### Scenario: Proveedor con retencion cero fuera de la lista
- **WHEN** el unico proveedor que sirve el modelo tiene retencion cero pero no esta en la lista cerrada
- **THEN** la llamada no se le asigna

### Requirement: Lista cerrada de proveedores por jurisdiccion
La lista de proveedores permitidos SHALL contener solo proveedores con sede en el Espacio Economico Europeo o en un pais con decision de adecuacion de la UE, segun la sede que publica el agregador. Un proveedor sin sede publicada SHALL quedar fuera. La lista SHALL ser cerrada: un proveedor que el agregador incorpore despues no recibe trafico hasta que se revise y se anada.

#### Scenario: Proveedor con sede en un pais sin decision de adecuacion
- **WHEN** un proveedor con sede en un pais sin decision de adecuacion sirve el modelo, aunque tenga retencion cero
- **THEN** no recibe ninguna llamada del sistema

#### Scenario: Proveedor sin sede publicada
- **WHEN** el agregador no publica la sede de un proveedor
- **THEN** ese proveedor no esta en la lista y no recibe ninguna llamada

#### Scenario: Proveedor nuevo en el agregador
- **WHEN** el agregador empieza a servir el modelo con un proveedor que no estaba en la lista
- **THEN** ese proveedor no recibe trafico mientras no se anada a la lista

### Requirement: Todo modelo primario tiene proveedor dentro de la politica
El modelo primario de cada modelo logico servido por el agregador SHALL tener al menos un proveedor que cumpla la politica completa. Un modelo que solo sirven proveedores excluidos no SHALL usarse como primario.

#### Scenario: Primario del revisor
- **WHEN** el unico proveedor de un modelo candidato a primario esta excluido por la lista
- **THEN** ese modelo no se usa como primario y el modelo logico pasa a otro modelo con proveedores dentro de la politica

### Requirement: Una politica que no puede cumplirse falla de forma explicita
Cuando ningun proveedor del agregador cumple la politica, la llamada al agregador SHALL fallar con un error que identifica la restriccion incumplida, sin asignarse a un proveedor que no la cumpla. A partir de ese error SHALL aplicarse el fallback del proxy como ante cualquier otro fallo del primario.

#### Scenario: Ningun proveedor cumple la politica y el modelo logico no tiene fallback
- **WHEN** se llama a un modelo logico sin fallback cuyo modelo no tiene ningun proveedor dentro de la politica
- **THEN** el cliente recibe un error (HTTP 404 del agregador) que nombra los proveedores disponibles y los permitidos, y ningun proveedor fuera de la politica recibe la peticion

#### Scenario: Ningun proveedor cumple la politica y el modelo logico tiene fallback
- **WHEN** se llama a un modelo logico con fallback cuyo modelo primario no tiene ningun proveedor dentro de la politica
- **THEN** el proxy desvia la llamada a su deployment de respaldo y la respuesta lo indica (numero de fallbacks intentados y modelo que respondio), aunque el agente no lo inspeccione

### Requirement: El respaldo fuera del agregador no esta cubierto por la politica
La politica SHALL aplicarse solo al trafico que pasa por el agregador. El trafico desviado a un deployment de respaldo de otro proveedor (Hugging Face) SHALL considerarse fuera de esta politica, y esa limitacion SHALL constar en la configuracion del proxy.

#### Scenario: Llamada desviada al respaldo
- **WHEN** una llamada del primario falla, por la politica o por cualquier otra causa, y el proxy la reintenta contra el respaldo de Hugging Face
- **THEN** el proveedor de inferencia de esa llamada lo elige Hugging Face, sin las restricciones de esta politica

### Requirement: Los parametros que envian los agentes no alteran la politica
Las llamadas de los agentes y del juez offline SHALL NOT enviar preferencias de enrutado de proveedor. Los parametros adicionales que si envian (metadata de trazas, formato de respuesta, esfuerzo de razonamiento) SHALL NOT sustituir ni relajar la politica del deployment.

#### Scenario: Llamada con metadata, formato de respuesta o razonamiento
- **WHEN** un agente envia metadata de trazas, un formato de respuesta o un esfuerzo de razonamiento en su llamada
- **THEN** la politica del deployment se aplica igual que sin esos parametros

### Requirement: Verificacion estatica de la politica de enrutado
El sistema SHALL verificar de forma estatica, a partir de la configuracion del proxy y sin red, modelo ni credenciales, que todo deployment que no es de respaldo de Hugging Face lleva la politica completa, de modo que la comprobacion corra en integracion continua en cada cambio.

#### Scenario: Configuracion con la politica completa
- **WHEN** se verifica una configuracion en la que todos los deployments del agregador llevan las tres restricciones
- **THEN** la verificacion pasa

#### Scenario: Deployment sin politica o con la politica incompleta
- **WHEN** se verifica una configuracion en la que un deployment del agregador no lleva la politica, permite la recoleccion de datos, no exige retencion cero o no tiene lista cerrada de proveedores
- **THEN** la verificacion SHALL fallar identificando el deployment y la restriccion que falta
