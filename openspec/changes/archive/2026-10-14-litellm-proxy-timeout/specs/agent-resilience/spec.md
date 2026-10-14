# Spec Delta

## ADDED Requirements

### Requirement: Timeout explicito en el proxy LiteLLM
El proxy LiteLLM SHALL fijar un timeout explicito para toda llamada que hace a un proveedor subyacente, independiente de cualquier timeout que los clientes (los agentes) configuren por su cuenta, de forma que una llamada colgada del lado del proveedor falle en un tiempo acotado sin depender de que el cliente la corte.

#### Scenario: El proveedor subyacente no responde
- **WHEN** una llamada de LiteLLM a un proveedor subyacente no recibe respuesta dentro del timeout configurado en el proxy
- **THEN** LiteLLM corta la llamada y devuelve un error de timeout al cliente, sin esperar mas alla de ese limite

#### Scenario: Una llamada normal no se ve afectada
- **WHEN** el proveedor subyacente responde dentro del tiempo habitual
- **THEN** la llamada se completa con normalidad, sin ningun cambio de comportamiento por este requisito
