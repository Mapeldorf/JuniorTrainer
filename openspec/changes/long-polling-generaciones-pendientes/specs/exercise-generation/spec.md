# Spec Delta

## ADDED Requirements

### Requirement: Espera larga para detectar cambios en las generaciones pendientes
El sistema SHALL ofrecer una forma de consultar las generaciones pendientes que responda en cuanto el conjunto de generaciones `generating`/`ready` cambie (alguna generación cambia de estado), y que, si no cambia nada, SHALL responder igualmente al cabo de un tiempo de espera acotado con el listado de pendientes vigente en ese momento. En ambos casos la respuesta SHALL tener el mismo contrato que el listado de generaciones pendientes.

#### Scenario: Una generación pendiente cambia de estado mientras se espera
- **WHEN** se consulta el listado de pendientes en modo de espera larga y, antes de que se cumpla el tiempo de espera, una generación pasa de `generating` a `ready` o a `error`
- **THEN** la respuesta llega de inmediato con el listado de pendientes actualizado

#### Scenario: Nada cambia durante la espera
- **WHEN** se consulta el listado de pendientes en modo de espera larga y ninguna generación cambia de estado antes de que se cumpla el tiempo de espera
- **THEN** la respuesta llega al cumplirse el tiempo de espera, con el listado de pendientes tal cual estaba

#### Scenario: No hay ninguna generación pendiente
- **WHEN** se consulta el listado de pendientes en modo de espera larga y no hay ninguna generación en curso ni lista para revisar
- **THEN** la respuesta llega al cumplirse el tiempo de espera, con una lista vacía

#### Scenario: Varias generaciones pendientes cambian en la misma espera
- **WHEN** dos generaciones pendientes cambian de estado mientras se espera
- **THEN** la respuesta llega con el listado reflejando ambos cambios, sin necesitar una segunda consulta para ver el segundo cambio
