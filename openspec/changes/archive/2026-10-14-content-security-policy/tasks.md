# Tasks

## 1. CSP en el backend

- [x] 1.1 En `backend/app/security_headers.py`, añadir `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'` a toda respuesta, y una CSP alternativa mas permisiva (permitiendo `cdn.jsdelivr.net`, `fonts.googleapis.com`/`fonts.gstatic.com` y `'unsafe-inline'`) solo cuando `scope["path"]` sea `/docs` o `/redoc`. Verificar que el modulo importa sin errores (`python -c "import ast; ast.parse(open('app/security_headers.py').read())"`).
- [x] 1.2 Levantar el backend localmente (`uvicorn app.main:app`) y verificar con `curl -i` que `GET /health` incluye `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'`. Verificado.
- [x] 1.3 Con el backend levantado, verificar con `curl -i GET /docs` y `curl -i GET /redoc` que ambos devuelven una `Content-Security-Policy` distinta a la de 1.2 (con `cdn.jsdelivr.net` permitido). Verificado via `curl` (cabecera correcta en ambas rutas); no se abrio Swagger UI/ReDoc en un navegador real para confirmar renderizado visual.

## 2. Eliminar el inline del build de produccion del frontend

- [x] 2.1 En `frontend/angular.json`, cambiar `optimization.styles` de `true` a `{ "minify": true, "inlineCritical": false }` en la configuracion `production`.
- [x] 2.2 En `frontend/src/index.html`, quitar el atributo `style="font-family: ..."` inline del `<body>` y sustituirlo por una clase Tailwind (`font-sans`).
- [x] 2.3 En `frontend/src/styles.css`, definir `--font-sans: 'Geist', system-ui, sans-serif;` dentro de un bloque `@theme` para que la clase `font-sans` siga aplicando la tipografia Geist.
- [x] 2.4 Ejecutar `ng build` (configuracion de produccion) y verificar en `dist/frontend/browser/index.html` que no queda ningun `<script>`, `<style>` ni atributo `style=""` inline (solo `<link>` externos y `<script src="...">`).

## 3. Cabeceras de seguridad y CSP en nginx

- [x] 3.1 En `frontend/nginx.conf`, añadir `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` y `Strict-Transport-Security: max-age=31536000; includeSubDomains` a toda respuesta (`add_header ... always` en el bloque `server`).
- [x] 3.2 En `frontend/nginx.conf`, añadir `Content-Security-Policy` con `default-src 'self'`, `script-src 'self'`, `style-src 'self' https://fonts.googleapis.com`, `font-src 'self' https://fonts.gstatic.com`, `img-src 'self' data:`, `connect-src 'self'` + la URL de la API y la de Supabase ya usadas en `frontend/src/environments/environment.ts`, `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`, `frame-ancestors 'none'` — sin `'unsafe-inline'` en ningun directive.
- [x] 3.3 Construir la imagen de produccion (`docker build -t jt-frontend-csp-check frontend`) y levantarla; verificar con `curl -i` que la respuesta incluye las cinco cabeceras de 3.1/3.2. Verificado.
- [ ] 3.4 Con el contenedor levantado, abrir la SPA en un navegador y verificar en la consola de DevTools que no hay ningun error de CSP (ni bloqueo de la fuente Geist, ni de las llamadas a la API/Supabase, ni de ningun script/estilo) recorriendo las pantallas principales (login, generar, revisar, mis bloques). Verificado parcialmente: la pantalla de login carga sin errores de consola ni de CSP (fuente Geist aplicada). Pendiente recorrer el resto de pantallas (generar, revisar, mis bloques), que requieren backend y Supabase reales con datos/sesion validos -- no disponibles en esta verificacion aislada.
