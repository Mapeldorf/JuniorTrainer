# frontend-security-headers Specification

## Purpose
Garantiza que toda respuesta del servidor que sirve el frontend Angular incluye un conjunto minimo de cabeceras de seguridad HTTP, incluida una Content-Security-Policy estricta que mitigue XSS, dado que es la unica superficie HTML real de la aplicacion.

## Requirements

### Requirement: Cabecera X-Content-Type-Options en toda respuesta
El sistema SHALL incluir la cabecera `X-Content-Type-Options: nosniff` en toda respuesta HTTP servida por el frontend.

#### Scenario: Carga de la SPA
- **WHEN** un navegador solicita cualquier ruta de la SPA
- **THEN** la respuesta incluye `X-Content-Type-Options: nosniff`

### Requirement: Cabecera X-Frame-Options en toda respuesta
El sistema SHALL incluir la cabecera `X-Frame-Options: DENY` en toda respuesta HTTP servida por el frontend, para impedir que la aplicacion se embeba en un `<iframe>` de otro origen.

#### Scenario: Carga de la SPA
- **WHEN** un navegador solicita cualquier ruta de la SPA
- **THEN** la respuesta incluye `X-Frame-Options: DENY`

### Requirement: Cabecera Referrer-Policy en toda respuesta
El sistema SHALL incluir la cabecera `Referrer-Policy: strict-origin-when-cross-origin` en toda respuesta HTTP servida por el frontend.

#### Scenario: Carga de la SPA
- **WHEN** un navegador solicita cualquier ruta de la SPA
- **THEN** la respuesta incluye `Referrer-Policy: strict-origin-when-cross-origin`

### Requirement: Cabecera Strict-Transport-Security en toda respuesta
El sistema SHALL incluir la cabecera `Strict-Transport-Security` con una duracion de al menos un año y `includeSubDomains` en toda respuesta HTTP servida por el frontend, independientemente de si la conexion actual es HTTP o HTTPS.

#### Scenario: Carga de la SPA
- **WHEN** un navegador solicita cualquier ruta de la SPA
- **THEN** la respuesta incluye una cabecera `Strict-Transport-Security` valida

### Requirement: Content-Security-Policy estricta sin inline
El sistema SHALL incluir en toda respuesta HTML servida por el frontend una cabecera `Content-Security-Policy` cuyo `default-src` sea `'self'`, que no incluya `'unsafe-inline'` ni `'unsafe-eval'` en ningun directive, y que solo permita como origenes externos los que la aplicacion necesita realmente para funcionar (la URL de la API/Supabase configuradas en el build).

#### Scenario: Carga de la SPA
- **WHEN** un navegador solicita `GET /` o cualquier ruta que resuelva a `index.html`
- **THEN** la respuesta incluye una `Content-Security-Policy` con `default-src 'self'`
- **AND** ningun directive de esa politica incluye `'unsafe-inline'` ni `'unsafe-eval'`

#### Scenario: El bundle de produccion no depende de contenido inline
- **WHEN** se genera el build de produccion del frontend
- **THEN** el `index.html` resultante no contiene ningun `<script>`, `<style>` ni atributo `style=""` inline
- **AND** la aplicacion sigue funcionando correctamente bajo la Content-Security-Policy sin `'unsafe-inline'`

#### Scenario: Sin origenes de fuentes externas
- **WHEN** se inspecciona la `Content-Security-Policy` servida por el frontend
- **THEN** ni `style-src` ni `font-src` incluyen `fonts.googleapis.com` ni `fonts.gstatic.com`
- **AND** la politica no permite ningun otro origen de fuentes externo, porque la aplicacion no carga fuentes web
