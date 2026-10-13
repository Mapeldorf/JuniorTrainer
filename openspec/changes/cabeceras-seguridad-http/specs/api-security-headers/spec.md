# Spec Delta

## Purpose

Garantiza que toda respuesta del backend incluye un conjunto minimo de cabeceras de seguridad HTTP estandar.

## ADDED Requirements

### Requirement: Cabecera X-Content-Type-Options en toda respuesta
El sistema SHALL incluir la cabecera `X-Content-Type-Options: nosniff` en toda respuesta HTTP, incluidas las de error.

#### Scenario: Respuesta de exito
- **WHEN** cualquier endpoint responde con exito
- **THEN** la respuesta incluye `X-Content-Type-Options: nosniff`

#### Scenario: Respuesta de error
- **WHEN** cualquier endpoint responde con un error (4xx o 5xx)
- **THEN** la respuesta incluye `X-Content-Type-Options: nosniff`

### Requirement: Cabecera X-Frame-Options en toda respuesta
El sistema SHALL incluir la cabecera `X-Frame-Options: DENY` en toda respuesta HTTP.

#### Scenario: Cualquier respuesta
- **WHEN** cualquier endpoint responde, con exito o con error
- **THEN** la respuesta incluye `X-Frame-Options: DENY`

### Requirement: Cabecera Referrer-Policy en toda respuesta
El sistema SHALL incluir la cabecera `Referrer-Policy: strict-origin-when-cross-origin` en toda respuesta HTTP.

#### Scenario: Cualquier respuesta
- **WHEN** cualquier endpoint responde, con exito o con error
- **THEN** la respuesta incluye `Referrer-Policy: strict-origin-when-cross-origin`

### Requirement: Cabecera Strict-Transport-Security en toda respuesta
El sistema SHALL incluir la cabecera `Strict-Transport-Security` con una duracion de al menos un año y `includeSubDomains` en toda respuesta HTTP, independientemente de si la conexion actual es HTTP o HTTPS.

#### Scenario: Cualquier respuesta
- **WHEN** cualquier endpoint responde, con exito o con error
- **THEN** la respuesta incluye una cabecera `Strict-Transport-Security` valida
