# Proposal

## Why

Una auditoria de seguridad detecto que no existe ninguna proteccion contra XSS via `Content-Security-Policy` en todo el proyecto. En el backend, la propuesta previa `cabeceras-seguridad-http` (ya archivada en `openspec/specs/api-security-headers/spec.md`) decidio explicitamente NO añadirla (ver su `design.md`, seccion Non-Goals) porque `/docs`/`/redoc` de FastAPI cargan JS/CSS de un CDN externo y romperian con una CSP estricta sin lista de origenes dedicada; esa decision queda obsoleta ahora que se define esa lista. En el frontend (SPA Angular servida por nginx) el hueco es mayor: no hay ninguna cabecera de seguridad, ni CSP ni las basicas que ya tiene el backend, pese a ser la unica superficie HTML real de la aplicacion y el lugar donde se renderiza contenido generado por LLM (enunciados de ejercicios, feedback de evaluacion) que, si no se escapara correctamente en algun punto, seria el vector que XSS explotaria. Es urgente por ese mismo motivo: ya hay contenido de origen no confiable llegando al navegador.

## What Changes

- Backend (`backend/app/security_headers.py`): añadir `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'` a toda respuesta de la API JSON, y una CSP mas permisiva acotada solo a `/docs` y `/redoc` (permite `cdn.jsdelivr.net` y el `<script>`/`<style>` inline que genera FastAPI para esas dos paginas).
- Frontend (`frontend/nginx.conf`): añadir las cabeceras que el backend ya tenia y el frontend nunca tuvo (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Strict-Transport-Security`) mas una `Content-Security-Policy` real (`default-src 'self'`, sin `unsafe-inline` en ningun directive).
- Para que la CSP del frontend pueda ir sin `unsafe-inline`, eliminar los dos unicos puntos de inline que el build de produccion de Angular inyectaba: el `<style>`/`<script>` de inlining de CSS critico (`frontend/angular.json`: `optimization.styles.inlineCritical: false`) y el atributo `style=""` inline en `frontend/src/index.html` (movido a una clase Tailwind definida via `@theme` en `frontend/src/styles.css`).

## Capabilities

### New Capabilities
- `frontend-security-headers`: cabeceras de seguridad HTTP (incluida CSP) presentes en toda respuesta del servidor nginx que sirve el frontend Angular, que hoy no tiene ninguna.

### Modified Capabilities
- `api-security-headers`: añade dos requirements nuevos (Content-Security-Policy restrictiva en la API JSON, y una CSP permisiva acotada a `/docs`/`/redoc`) sobre el capability ya archivado en `openspec/specs/api-security-headers/spec.md` (propuesta `cabeceras-seguridad-http`). Los cuatro requirements existentes (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Strict-Transport-Security`) no cambian.

## Impact

- `backend/app/security_headers.py`: logica de CSP condicionada por path (`/docs`, `/redoc` vs resto).
- `frontend/nginx.conf`: nuevas `add_header` en el bloque `server`.
- `frontend/angular.json`, `frontend/src/index.html`, `frontend/src/styles.css`: cambios no funcionales para eliminar el inline que la CSP estricta no permite.
- Sin cambios en routers, schemas, ni en el contrato de ningun endpoint; sin nueva dependencia.
