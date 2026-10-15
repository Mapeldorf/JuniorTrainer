# Tasks

## 1. Fundamentos del tema y tipografía

- [x] 1.1 En `frontend/src/styles.css`, sustituir el `@theme` actual por los tokens del tema oscuro (`--color-surface`, `--color-surface-raised`, `--color-border`, `--color-content`, `--color-muted`, `--color-primary`, `--color-danger`, `--color-success`, `--color-warning`), el stack de fuentes del sistema para `--font-sans` y `--font-mono`, y `--app-max-width`. Verificar con `ng build` que compila y que las utilidades de token (`bg-surface`, `text-content`, `border-border`, `text-primary`, …) existen.
- [x] 1.2 En `frontend/src/styles.css`, añadir en `@layer components` las primitivas compartidas (`.app-container`, `.card`, `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.input`, `.label`, `.badge`, `.alert-error`, `.focus-ring`). Verificar con `ng build` que compila y que una plantilla de prueba puede usar esas clases.
- [x] 1.3 En `frontend/src/index.html`, eliminar los `<link>` de Google Fonts (Geist y Geist Mono) y cambiar las clases del `<body>` del tema claro (`bg-zinc-50 text-zinc-900`) por el tema oscuro. Verificar que `ng build` compila y que el `index.html` resultante no contiene referencias a `fonts.googleapis.com`/`fonts.gstatic.com`.
- [x] 1.4 En `frontend/nginx.conf`, quitar `https://fonts.googleapis.com` de `style-src` y `https://fonts.gstatic.com` de `font-src` de la `Content-Security-Policy`. Verificar leyendo el fichero que la política ya no menciona ningún origen de fuentes externas y que mantiene `default-src 'self'` sin `'unsafe-inline'`/`'unsafe-eval'` (delta de `frontend-security-headers`).

## 2. Componentes compartidos

- [x] 2.1 Migrar `frontend/src/app/core/brand-mark.ts` al tema (superficie/acento del tema, tipografía de sistema) usando las primitivas del grupo 1. Verificar con `ng test` que sus specs siguen en verde.
- [x] 2.2 Migrar `frontend/src/app/core/confirm-dialog.html` al tema oscuro (panel con superficie elevada y borde del tema, overlay, botones primario/secundario/peligro con las primitivas y el anillo de foco). Verificar con `ng test` que las specs del diálogo (renderizado, botones, Escape) siguen en verde.
- [x] 2.3 Migrar `frontend/src/app/tech-lead/tech-lead-nav/tech-lead-nav.html` al tema (fondo de superficie, borde inferior, estado activo de `routerLinkActive` con el acento del tema). Verificar con `ng test` que sus specs siguen en verde.

## 3. Pantallas de auth y home

- [x] 3.1 Migrar `frontend/src/app/auth/login/login.html` al tema oscuro (panel izquierdo, formulario, inputs, botón, enlace de olvido y mensaje de error con las primitivas). Verificar con `ng test` sobre `login` que sus specs siguen en verde.
- [x] 3.2 Migrar `frontend/src/app/auth/forgot/forgot.html` al tema. Verificar con `ng test` sobre `forgot` que sus specs siguen en verde.
- [x] 3.3 Migrar `frontend/src/app/auth/set-password/set-password.html` al tema (incluido el aviso de enlace no válido y los errores). Verificar con `ng test` sobre `set-password` que sus specs siguen en verde.
- [ ] 3.4 Migrar `frontend/src/app/home/home.html` al tema. Verificar con `ng test` que `home` sigue en verde y comprobar a ojo en `ng serve` que las cuatro pantallas de este grupo usan fondo oscuro, tipografía de sistema y ancho estrecho.

## 4. Pantallas de alumno

- [x] 4.1 Migrar `frontend/src/app/student/mis-bloques/mis-bloques.html` al tema (tarjetas de bloque, secciones pendientes/hechos, botones). Verificar con `ng test` sobre `mis-bloques` que sus specs siguen en verde.
- [x] 4.2 Migrar `frontend/src/app/student/ejercicio/ejercicio.html` al tema (selector de posiciones, tarjeta del ejercicio, bloque de código legible, textarea, y colores de veredicto correcto/incompleto/incorrecto sobre fondo oscuro). Verificar con `ng test` sobre `ejercicio` que sus specs siguen en verde.
- [ ] 4.3 Comprobar a ojo en `ng serve` las dos pantallas de alumno: tema oscuro consistente, bloque de código legible, veredictos distinguibles y navegación con teclado con foco visible.

## 5. Pantallas de tech-lead

- [x] 5.1 Migrar `frontend/src/app/tech-lead/ejercicios/ejercicios.html` al tema (lista de generaciones, estados, filtros, tabla de guardados y botón de eliminar). Verificar con `ng test` sobre `ejercicios` que sus specs siguen en verde.
- [x] 5.2 Migrar `frontend/src/app/tech-lead/revisar/revisar.html` al tema. Verificar con `ng test` sobre `revisar` que sus specs siguen en verde.
- [x] 5.3 Migrar `frontend/src/app/tech-lead/generar/generar.html` al tema. Verificar con `ng test` sobre `generar` que sus specs siguen en verde.
- [x] 5.4 Migrar `frontend/src/app/tech-lead/bloques/bloques.html` al tema. Verificar con `ng test` sobre `bloques` que sus specs siguen en verde.
- [x] 5.5 Migrar `frontend/src/app/tech-lead/bloque-detalle/bloque-detalle.html` al tema. Verificar con `ng test` sobre `bloque-detalle` que sus specs siguen en verde.
- [x] 5.6 Migrar `frontend/src/app/tech-lead/bloque-editar/bloque-editar.html` al tema. Verificar con `ng test` sobre `bloque-editar` que sus specs siguen en verde.
- [x] 5.7 Migrar `frontend/src/app/tech-lead/alumnos/alumnos.html` al tema. Verificar con `ng test` sobre `alumnos` que sus specs siguen en verde.
- [x] 5.8 Migrar `frontend/src/app/tech-lead/alumno-detalle/alumno-detalle.html` al tema. Verificar con `ng test` sobre `alumno-detalle` que sus specs siguen en verde.
- [ ] 5.9 Comprobar a ojo en `ng serve` las pantallas de tech-lead: nav y tablas consistentes con el tema, estados legibles y contenedor centrado y estrecho.

## 6. Verificación final

- [x] 6.1 Ejecutar la suite completa del frontend (`ng test --watch=false`) y confirmar que sigue en verde (el cambio es presentacional y no debe romper ningún test de comportamiento).
- [x] 6.2 Ejecutar `ng build` en configuración de producción y confirmar que compila sin errores de presupuesto de estilos ni de plantillas.
- [ ] 6.3 Recorrido visual completo por todas las pantallas en `ng serve` (auth, home, alumno, tech-lead y diálogo de confirmación): tema oscuro uniforme, tipografía de sistema, ancho estrecho, foco visible con teclado, y sin restos de clases del tema claro (`bg-white`, `bg-zinc-50`, `text-zinc-900`).
