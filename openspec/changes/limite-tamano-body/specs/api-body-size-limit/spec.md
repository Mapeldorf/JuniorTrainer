# Spec Delta

## Purpose

Rechaza las peticiones HTTP cuyo body supere un tamaño maximo, para evitar que un payload arbitrariamente grande agote memoria o CPU del backend.

## ADDED Requirements

### Requirement: Rechazo por Content-Length declarado
El sistema SHALL rechazar con `413 Content Too Large` cualquier peticion cuyo header `Content-Length` declare un tamaño superior al limite configurado, sin leer el body.

#### Scenario: Content-Length por encima del limite
- **WHEN** una peticion llega con `Content-Length` mayor que el limite configurado
- **THEN** el sistema responde `413 Content Too Large` sin invocar el endpoint ni el parseo de Pydantic

### Requirement: Rechazo por tamaño real cuando no hay Content-Length fiable
El sistema SHALL cortar la lectura y rechazar con `413 Content Too Large` cualquier peticion cuyo body, contado por los bytes realmente recibidos, supere el limite configurado, incluso si no trae `Content-Length` o este no coincide con el tamaño real.

#### Scenario: Body chunked sin Content-Length que supera el limite
- **WHEN** una peticion sin `Content-Length` (o con uno menor al real) envia mas bytes de body que el limite configurado
- **THEN** el sistema corta la conexion y responde `413 Content Too Large` en cuanto se supera el limite, sin esperar a que el cliente termine de enviar el resto del body

### Requirement: Peticiones dentro del limite no se ven afectadas
El sistema SHALL procesar con normalidad cualquier peticion cuyo body este por debajo del limite configurado, sin cambios de comportamiento respecto a hoy.

#### Scenario: Body dentro del limite
- **WHEN** una peticion autenticada envia un body por debajo del limite configurado
- **THEN** el endpoint correspondiente procesa la peticion igual que antes de este cambio

### Requirement: Respuesta sin detalles internos al superar el limite
El sistema SHALL devolver, cuando se rechaza una peticion por tamaño de body, una respuesta `413` cuyo cuerpo no exponga el valor exacto del limite ni configuracion interna, mas alla de informar que el body es demasiado grande.

#### Scenario: Cuerpo de la respuesta 413
- **WHEN** una peticion se rechaza por superar el limite de tamaño de body
- **THEN** el cuerpo de la respuesta indica unicamente que el body es demasiado grande, sin datos de configuracion interna
