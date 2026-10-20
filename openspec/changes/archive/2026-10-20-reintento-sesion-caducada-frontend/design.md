# Design

## Context

`authInterceptor` (`frontend/src/app/core/auth.interceptor.ts`) adjunta el `access_token` de la sesion de Supabase a toda peticion hacia FastAPI. El backend valida ese token contra Supabase Auth en cada peticion (`app/deps.py`) y responde 401 si lo rechaza. Hasta ahora el interceptor no distinguia entre "no hay sesion" y "el backend rechazo el token que si se envio": en el segundo caso, se propagaba el 401 sin mas, dejando a quien llamaba (un componente, un guard) con un error generico aunque la sesion pudiera renovarse. Ver proposal.md - Why.

## Goals / Non-Goals

**Goals:**
- Recuperar peticiones que fallan por un access token caducado momentos antes de llegar al backend, sin intervencion del usuario.
- Cuando la sesion ya no es recuperable (el refresh token tambien es invalido), dejar la app en un estado coherente: sesion local cerrada y en la pantalla de login, no un 401 silencioso en consola.

**Non-Goals:**
- No se cambia el comportamiento del backend (`app/deps.py` sigue devolviendo 401 igual que antes); el fix es puramente del lado del cliente.
- No se implementa reintento para codigos de error distintos de 401 (403, 404, 5xx siguen propagandose tal cual).
- No se persigue eliminar por completo la causa raiz del access token caducado del lado de Supabase (temporizador de `autoRefreshToken`, sesgo de reloj, etc.); este cambio es una red de seguridad reactiva, no una correccion de esa causa.

## Decisions

- **Reintento reactivo en el interceptor (catchError sobre next(req)) en vez de refresco proactivo antes de cada peticion**: `getSession()` ya intenta refrescar cuando detecta expiracion local, asi que anadir una renovacion incondicional antes de cada peticion duplicaria trabajo en el caso normal. Reaccionar solo al 401 real del backend cubre tanto la expiracion detectada a tiempo como los casos en que `getSession()` creyo el token valido (sesgo de reloj, invalidacion del lado de Supabase) sin coste añadido en el camino feliz.
- **Un unico reintento, no un bucle**: si el segundo intento (con el token renovado) tambien devuelve 401, no se vuelve a intentar renovar. Evita un bucle de reintentos contra un backend que rechaza sistematicamente (p.ej. problema de reloj del servidor) y mantiene el comportamiento predecible: como mucho una renovacion por peticion.
- **En fallo de renovacion: `signOut()` + redirigir a `/login` + propagar igualmente el error**: se descarto quedarse solo con el 401 propagado (deja al usuario viendo un error de red sin saber que su sesion murio) y se descarto resolver el observable sin error (el componente que pidio los datos nunca se entera de que la peticion no se completo). Haciendo ambas cosas, el usuario aterriza en login y el componente llamador puede seguir reaccionando al error si lo necesita (p.ej. apagar un spinner).
- **La logica vive en el interceptor, no en cada servicio o componente**: todas las llamadas a la API pasan por aqui (`AssignmentsApiService`, etc.), asi que es el unico punto donde interceptar el 401 cubre todos los endpoints sin tocarlos uno a uno.

## Risks / Trade-offs

- [Una peticion que falla por 401 por una razon ajena a la sesion (p.ej. una regla de autorizacion especifica que decidiera usar 401 en vez de 403) dispararia igualmente el intento de renovacion] → Hoy el backend reserva 401 exclusivamente para fallos de autenticacion (ver `openspec/specs/user-auth/spec.md` - Requirement: Sesion mediante JWT de Supabase) y 403 para autorizacion, asi que no hay colision conocida; si eso cambiara, habria que revisar este interceptor.
- [Varias peticiones en paralelo que reciben 401 a la vez disparan varias renovaciones de sesion casi simultaneas] → El SDK de Supabase ya serializa internamente las renovaciones concurrentes (lock interno de `auth-js`), asi que no se evalua necesario anadir coordinacion adicional en el interceptor.
- [Redirigir a `/login` en mitad de una tarea del usuario (p.ej. a medio escribir una respuesta) pierde ese trabajo en curso] → Aceptado: la sesion ya esta muerta, no hay forma de completar la peticion igualmente; es preferible a dejar la app en un estado colgado. Fuera de alcance de este cambio recuperar el borrador tras volver a iniciar sesion.

## Migration Plan

Cambio de cliente sin migracion de datos ni de API. Se despliega con el build normal del frontend; no requiere coordinacion con el backend. Rollback: revertir el commit del frontend.
