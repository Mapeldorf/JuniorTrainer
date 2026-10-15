# Design

## Context

Ver `proposal.md` - Why. El frontend es Angular 22 standalone con signals y Tailwind v4, sin Angular CDK ni librería de componentes UI: el estilo vive como clases utilitarias directamente en cada plantilla. `src/styles.css` hoy solo importa Tailwind y define `--font-sans: 'Geist'`; `index.html` carga Geist y Geist Mono desde Google Fonts y fija el tema claro en el `<body>` (`bg-zinc-50 text-zinc-900`). Hay ~14 plantillas (auth, home, alumno, tech-lead) que repiten los mismos patrones: fondo `bg-zinc-50`, tarjeta `rounded-xl border border-zinc-200 bg-white`, botón primario `bg-blue-700 hover:bg-blue-800`, botón secundario `border-zinc-300 hover:bg-zinc-100`, campo `border-zinc-300 focus:border-blue-700`, y errores `bg-red-100 text-red-900`. La CSP de producción (`nginx.conf`) permite `fonts.googleapis.com`/`fonts.gstatic.com`; el dev-server de Angular no aplica esas cabeceras.

## Goals / Non-Goals

**Goals:**
- Un tema oscuro único definido por tokens de Tailwind v4, aplicable sin tocar lógica.
- Un conjunto pequeño y compartido de clases de componente (superficie, botón, campo, badge, contenedor) que sustituya las clases duplicadas.
- Tipografía de sistema tipo Apple sin ninguna fuente web.
- Un ancho de contenido estrecho y centrado, consistente entre pantallas.

**Non-Goals:**
- Modo claro o conmutador de tema (decidido: tema oscuro único).
- Introducir una librería de componentes UI o Angular CDK.
- Rediseñar la estructura de navegación, rutas o el contenido de cada pantalla; solo su presentación.
- Animaciones o microinteracciones complejas.

## Decisions

**Tema oscuro mediante tokens semánticos en `@theme` (Tailwind v4), no por pantalla.** Se definen variables `--color-surface`, `--color-surface-raised`, `--color-border`, `--color-content`, `--color-muted`, `--color-primary`, `--color-danger`, `--color-success`, `--color-warning` en `src/styles.css`, de forma que las utilidades (`bg-surface`, `text-content`, `border-border`, `text-primary`…) existen en todo el proyecto. Paleta base: fondo `zinc-950`, superficie `zinc-900`, superficie elevada `zinc-800`, borde `zinc-800`/`zinc-700`, texto `zinc-100`, texto atenuado `zinc-400`; acento azul subido de `blue-700` a `blue-500`/`blue-600` (el azul-700 actual no da contraste suficiente sobre fondo oscuro); estados `green-400`, `amber-400`, `red-400`/`red-500`. Alternativa descartada: un dark mode de Tailwind con `dark:` y conmutador de clase — añade complejidad y una segunda paleta que nadie pidió.

**Primitivas de UI como clases de componente en `@layer components` (CSS), no como componentes Angular.** Se añaden clases reutilizables (p. ej. `.app-container`, `.card`, `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.input`, `.label`, `.badge`, `.alert-error`, `.focus-ring`) que encapsulan los patrones repetidos, y las plantillas las combinan con utilidades de layout. Alternativa descartada: componentes Angular standalone por primitiva (Button, Card, Input) — más boilerplate, más ficheros y más tests para algo puramente presentacional, y rompe el estilo actual de "clases en la plantilla". Las clases en CSS sí siguen el enfoque Tailwind del proyecto y centralizan el cambio.

**Contenedor estrecho vía token de ancho máximo.** Se define `--app-max-width` (≈ `64rem`) y la clase `.app-container` (`mx-auto`, `max-w`, padding lateral reducido). Las pantallas de lectura (auth, home, alumno) usan además su propia medida (`~42rem`) para la línea de texto; las tablas de tech-lead usan el ancho del contenedor de la app. El ancho concreto es un valor de token, ajustable sin tocar plantillas.

**Tipografía: stack de sistema, se eliminan las fuentes web.** `--font-sans` pasa a `-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`, y se añade `--font-mono` de sistema (`ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, monospace`) para los bloques de código (hoy usan Geist Mono). Se eliminan los `<link>` de Google Fonts de `index.html`. Consecuencia directa: la CSP deja de necesitar los orígenes de fuentes (delta en `frontend-security-headers`).

**El `<body>` deja de fijar el tema claro.** Las clases `bg-zinc-50 text-zinc-900` pasan a las del tema oscuro (o se aplican desde `styles.css`), de modo que el fondo correcto se ve incluso antes de montar el componente raíz.

**Estados de foco accesibles y consistentes.** Una clase `.focus-ring` (`focus-visible:ring-2 ring-primary ring-offset-2 ring-offset-surface`) se aplica a botones, enlaces, campos y al selector de posiciones del ejercicio; los estados deshabilitados usan opacidad + `cursor` coherentes en todo el tema.

## Risks / Trade-offs

- [Contraste insuficiente en algún estado sobre fondo oscuro (accesibilidad)] → usar tokens con contraste AA sobre `zinc-950`/`zinc-900`, y revisar a ojo cada pantalla con la checklist de verificación de las tareas.
- [El cambio toca ~14 plantillas a la vez; riesgo de dejar alguna sin migrar o con clases mezcladas claro/oscuro] → inventariar las plantillas en las tareas y migrarlas por grupos (auth/home, alumno, tech-lead, compartidos), con verificación visual por grupo.
- [Interacción de `@theme` + `@layer components` en Tailwind v4 (orden de capas, purge de clases usadas solo en CSS)] → verificar que `ng build` compila y que las utilidades de token (`bg-surface`, etc.) existen; las clases de `@layer components` referencian utilidades, no al revés.
- [Cambiar la tipografía altera ligeramente métricas de layout] → irrelevante funcionalmente; los tests de componentes no dependen de métricas.
- [La CSP solo se aplica en producción (nginx); en dev no hay cabeceras] → el cambio de CSP se verifica sobre `nginx.conf` y, si se puede, contra una imagen construida; no se espera efecto en `ng serve`.

## Migration Plan

Cambio puramente de frontend, sin datos ni API. Un único PR: tokens + primitivas en `styles.css`, `index.html` sin fuentes web, plantillas migradas y `nginx.conf` con la CSP ajustada. Despliegue normal (build + servir). Rollback: revertir el commit/PR; al no haber cambios de esquema ni de contrato, no hace falta plan de datos.

## Open Questions

- Tono exacto del acento azul (`blue-500` vs `blue-600`) y valor final de `--app-max-width`: ajustables durante la implementación sin cambiar specs ni enfoque.
