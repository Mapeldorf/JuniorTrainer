# Spec Delta

## ADDED Requirements

### Requirement: Buscar ejercicios manualmente en el selector del formulario de bloque
El formulario de crear/editar bloque SHALL mantener el texto escrito en el campo de busqueda del selector de ejercicios como un borrador que no recarga el listado por si solo; el listado SHALL recargarse por texto unicamente cuando el tech lead confirma la busqueda pulsando un boton "Buscar" o la tecla Enter en el campo. El filtro por tipo SHALL seguir recargando el listado automaticamente al cambiarlo, sin necesidad de confirmacion.

#### Scenario: Escribir sin confirmar no lanza busqueda
- **WHEN** un tech lead escribe texto en el campo de busqueda del selector de ejercicios sin pulsar "Buscar" ni Enter
- **THEN** el listado de ejercicios no se recarga y sigue mostrando los resultados de la ultima busqueda confirmada

#### Scenario: Confirmar la busqueda con el boton
- **WHEN** un tech lead escribe un texto en el campo de busqueda y pulsa el boton "Buscar"
- **THEN** el listado se recarga mostrando los ejercicios que coinciden con ese texto

#### Scenario: Confirmar la busqueda con Enter
- **WHEN** un tech lead escribe un texto en el campo de busqueda y pulsa Enter
- **THEN** el listado se recarga mostrando los ejercicios que coinciden con ese texto, igual que si hubiera pulsado "Buscar"

#### Scenario: Cambiar el filtro de tipo sigue siendo automatico
- **WHEN** un tech lead cambia el filtro de tipo en el selector de ejercicios
- **THEN** el listado se recarga inmediatamente con ese filtro, sin necesidad de pulsar "Buscar"
