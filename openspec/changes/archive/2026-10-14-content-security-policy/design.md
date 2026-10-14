# Design

## Context

Ver `proposal.md` para la motivacion. Estado tecnico relevante:

- Backend: `backend/app/security_headers.py` ya añade cuatro cabeceras basicas via un middleware ASGI puro que envuelve `send()` (propuesta `cabeceras-seguridad-http`, archivada en `openspec/specs/api-security-headers/spec.md`). FastAPI expone `/docs` y `/redoc` con `docs_url`/`redoc_url` por defecto (no hay `Settings` para desactivarlos por entorno); ambos cargan su bundle (Swagger UI / ReDoc) desde `cdn.jsdelivr.net` y generan un `<script>` inline con la URL del `openapi.json` interpolada en cada respuesta, por lo que no es hasheable de forma estatica.
- Frontend: SPA Angular (`frontend/`), build de produccion servido por `nginx:1.27-alpine` con un `nginx.conf` sin ninguna cabecera hoy. El build de produccion de Angular (con Tailwind v4) inyecta por defecto, via el plugin `beasties`, un `<style>` con el CSS critico y un `<script>` inline que intercambia el `media` de la hoja de estilos diferida; el `index.html` fuente ademas tenia un atributo `style=""` inline en `<body>`. Los origenes externos reales que la SPA necesita en runtime, fijados en `frontend/src/environments/environment.ts` en tiempo de build, son `fonts.googleapis.com`/`fonts.gstatic.com` (tipografia Geist) y las URLs de la API propia y de Supabase (`apiUrl`, `supabaseUrl`).

## Goals / Non-Goals

**Goals:**
- CSP real (`default-src 'self'` o mas estricto) en ambas superficies, sin `'unsafe-inline'` ni `'unsafe-eval'` en ningun directive salvo la excepcion acotada de `/docs`/`/redoc`.
- No romper la documentacion interactiva de la API ni la build de produccion del frontend.
- No depender de infraestructura nueva (sin nonce dinamico por request, sin SSR, sin proxy adicional).

**Non-Goals:**
- No se decide aqui si `/docs`/`/redoc` deben desactivarse en produccion (misma decision diferida que dejo `cabeceras-seguridad-http`); esta propuesta solo acota su CSP para que no rompan.
- No se parametriza `connect-src` del frontend por entorno (p. ej. via `envsubst` en el arranque del contenedor nginx): hoy `apiUrl`/`supabaseUrl` ya se fijan en tiempo de build en `environment.ts`, y la CSP de nginx sigue el mismo patron (valores fijos en `nginx.conf`). Parametrizar ambos a la vez seria una propuesta aparte sobre configuracion de despliegue, no sobre CSP.
- No se añade Subresource Integrity (SRI) a la hoja de Google Fonts: el riesgo que mitigaria (CDN de Google comprometido) es ortogonal al XSS que esta propuesta ataja.

## Decisions

- **CSP del backend condicionada por path, no global.** Alternativa descartada: una unica CSP permisiva para toda la API que incluyera `cdn.jsdelivr.net`. Se descarta porque ampliaria innecesariamente la politica de todas las respuestas JSON (que no cargan nada) solo para cubrir dos rutas de documentacion. El middleware ya existente (`SecurityHeadersMiddleware`) decide la CSP mirando `scope["path"]` antes de añadir la cabecera.
- **Eliminar el inline del build de Angular en vez de permitirlo con `'unsafe-inline'` o hashes.** Alternativas consideradas:
  - `'unsafe-inline'` en `style-src`/`script-src`: descartada, anula la proteccion que se esta añadiendo (un XSS que inyecte un `<script>` inline tambien se ejecutaria).
  - Hashear el contenido inline (`'sha256-...'`): descartada para el `<style>` critico porque su contenido cambia en cada build (Tailwind regenera el CSS critico segun que componentes existan), lo que obligaria a regenerar el hash en cada deploy sin automatizacion nueva; mas fragil que desactivar el inlining.
  - Desactivar `optimization.styles.inlineCritical` en `angular.json`: elegida. Angular simplemente no inyecta ese `<style>`/`<script>`; el CSS pasa a cargarse como `<link>` normal (ya cacheado por el navegador en visitas repetidas), coste de performance aceptable (una peticion CSS adicional en la primera carga) a cambio de poder tener CSP estricta sin mantenimiento de hashes.
  - El atributo `style=""` inline en `index.html` se mueve a una clase Tailwind (`font-sans`) con `--font-sans` redefinido via `@theme` en `styles.css`, sin libreria ni mecanismo nuevo.
- **Valores de `connect-src`/`style-src`/`font-src` fijos en `nginx.conf`, iguales a los que ya usa `environment.ts`.** Mantiene un unico lugar de la verdad implicito (ambos ficheros deben listar los mismos origenes externos); no se extrae a una variable compartida porque son stacks distintos (TypeScript vs. nginx) sin mecanismo de build compartido hoy.

## Risks / Trade-offs

- [Desactivar `inlineCritical` retrasa ligeramente el primer render (First Contentful Paint) porque el CSS deja de estar inline y pasa a ser una peticion de red adicional] → Mitigacion: el fichero de estilos ya se cachea igual que el resto de assets con `outputHashing: all`; en visitas repetidas el coste es nulo, y es el precio estandar de evitar `'unsafe-inline'` en cualquier SPA con build estatico.
- [Si en el futuro se añade una libreria de frontend que requiera estilos/scripts inline (p. ej. un widget de terceros), la CSP estricta la rompera sin aviso previo hasta que se pruebe manualmente] → Mitigacion: el requirement de spec deja constancia explicita de "sin `'unsafe-inline'` ni `'unsafe-eval'`"; cualquier cambio futuro que lo necesite debe pasar por una revision explicita de la CSP, no añadirlo silenciosamente.
- [Los origenes de `connect-src`/`style-src`/`font-src` estan duplicados a mano entre `environment.ts` y `nginx.conf`; si cambia la URL de la API o de Supabase hay que actualizar los dos sitios] → Mitigacion: ambos cambios ya eran necesarios hoy (sin esta propuesta) para que la app siguiera funcionando; esta propuesta no añade un tercer lugar, solo lo deja documentado aqui como riesgo conocido.
