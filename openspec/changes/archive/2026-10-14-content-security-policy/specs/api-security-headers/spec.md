# Spec Delta

## ADDED Requirements

### Requirement: Content-Security-Policy restrictiva en la API JSON
El sistema SHALL incluir en toda respuesta de la API (cualquier ruta distinta de `/docs` y `/redoc`) una cabecera `Content-Security-Policy` que no permita ejecutar ni cargar ningun recurso activo (`default-src 'none'`), ademas de impedir el embebido en frames (`frame-ancestors 'none'`) y restringir el elemento `<base>` (`base-uri 'none'`).

#### Scenario: Respuesta JSON de exito
- **WHEN** un endpoint de negocio responde con exito
- **THEN** la respuesta incluye una `Content-Security-Policy` con `default-src 'none'`

#### Scenario: Respuesta JSON de error
- **WHEN** un endpoint de negocio responde con un error (4xx o 5xx)
- **THEN** la respuesta incluye una `Content-Security-Policy` con `default-src 'none'`

### Requirement: Content-Security-Policy permisiva acotada a la documentacion interactiva
El sistema SHALL incluir en las respuestas de `/docs` y `/redoc` una `Content-Security-Policy` distinta a la del resto de la API, que permita unicamente los origenes y mecanismos que Swagger UI y ReDoc necesitan para funcionar (el CDN que sirve su bundle, sus hojas de estilo y el `<script>` inline que generan con la URL del `openapi.json`), sin relajar la politica del resto de la API.

#### Scenario: Acceso a /docs
- **WHEN** un cliente solicita `GET /docs`
- **THEN** la respuesta incluye una `Content-Security-Policy` que permite cargar el bundle de Swagger UI desde su CDN y ejecutar su `<script>` inline
- **AND** no incluye `default-src 'none'`

#### Scenario: Acceso a /redoc
- **WHEN** un cliente solicita `GET /redoc`
- **THEN** la respuesta incluye una `Content-Security-Policy` que permite cargar el bundle de ReDoc desde su CDN y ejecutar su `<script>` inline
- **AND** no incluye `default-src 'none'`
