# Proposal

## Why

La interfaz actual del frontend es clara y funcional, pero visualmente genérica (fondo `zinc-50`, tarjetas blancas, acento `blue-700`, tipografía Geist cargada desde Google Fonts) y con layouts anchos (`px-8`, contenido a `max-w-[720px]`) que estiran la línea de lectura y repiten las mismas clases de tarjeta, botón y campo en cada plantilla. Se quiere una identidad más moderna y sobria —tema oscuro, tipografía tipo Apple, interfaz más estrecha— y, de paso, un lenguaje visual compartido que reduzca esa repetición.

## What Changes

- **BREAKING (visual)**: toda la aplicación pasa de tema claro a un **tema oscuro único** (sin conmutador): superficies oscuras, texto claro y contraste verificado. Los colores `bg-white`/`bg-zinc-50`/`text-zinc-900` dejan de usarse como base.
- **BREAKING (visual)**: se abandona la fuente web Geist y se adopta un **stack de fuentes del sistema** que prioriza SF Pro en dispositivos Apple (`-apple-system`, `BlinkMacSystemFont`, `"SF Pro Text"`) con alternativas nativas por plataforma (Segoe UI, Roboto). Se eliminan los `<link>` a Google Fonts de `index.html`, con lo que la aplicación deja de hacer peticiones externas de fuentes.
- La interfaz se **estrecha**: se introduce un contenedor/shell de aplicación con ancho máximo y centrado, padding lateral reducido y una medida de lectura cómoda, en lugar del `px-8` a pantalla completa actual.
- Se introducen **tokens de diseño** (variables de tema de Tailwind) y un conjunto pequeño de **primitivas de UI compartidas** (superficie/tarjeta, botón primario y secundario, campo de entrada, badge/estado, encabezado de página) que sustituyen las clases duplicadas hoy en cada plantilla.
- Se revisan estados de **hover, foco visible y deshabilitado** para que sean consistentes y accesibles sobre fondo oscuro, incluido el bloque de código (`<pre>`) y el diálogo de confirmación.
- Se actualiza la CSP para dejar de permitir los orígenes de Google Fonts, que ya no se usan.
- Se aplica el rediseño a **todas las pantallas**: auth (login, forgot, set-password), home, alumno (mis-bloques, ejercicio) y tech-lead (nav, ejercicios, revisar, generar, bloques, bloque-detalle, bloque-editar, alumnos, alumno-detalle), además de `brand-mark` y `confirm-dialog`.

## Capabilities

### New Capabilities
- `frontend-ui-theme`: el lenguaje visual de la aplicación — tema oscuro, tipografía de sistema, ancho y ritmo del layout, primitivas de UI compartidas y estados de interacción accesibles — como comportamiento observable y consistente en todas las pantallas.

### Modified Capabilities
- `frontend-security-headers`: la `Content-Security-Policy` deja de permitir `https://fonts.googleapis.com` (en `style-src`) y `https://fonts.gstatic.com` (en `font-src`), porque la aplicación ya no carga fuentes web y no los necesita.

## Impact

- **Tema y tipografía**: `frontend/src/styles.css` (tokens de tema), `frontend/src/index.html` (clases del `<body>`, eliminación de `<link>` de fuentes), `frontend/nginx.conf` (CSP sin orígenes de Google Fonts).
- **Layout y primitivas compartidas**: nuevo shell/encabezado de aplicación y clases o componentes de UI reutilizables en `frontend/src/app/core/`.
- **Plantillas modificadas**: `frontend/src/app/auth/**`, `home/home.html`, `student/**`, `tech-lead/**`, `core/brand-mark.ts`, `core/confirm-dialog.html`.
- **Sin cambios** en backend, rutas, lógica de negocio, servicios de datos ni contratos de API. Los tests existentes de componentes deben seguir en verde (el rediseño es presentacional).
- Riesgo de contraste/accesibilidad y de regresiones visuales al migrar muchas plantillas a la vez; se mitiga con los tokens compartidos y una verificación visual por pantalla.
