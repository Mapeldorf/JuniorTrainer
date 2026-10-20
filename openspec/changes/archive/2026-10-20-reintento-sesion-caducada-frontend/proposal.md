# Proposal

## Why

Al enviar la respuesta de un ejercicio (`POST /assignments/{id}/exercises/{id}/answer`), el backend devolvio 401 "Token invalido o caducado" aunque el frontend si mandaba un token: `getSession()` lo daba por valido localmente, pero habia caducado (o fue rechazado por Supabase) justo antes de llegar al backend. El interceptor de autenticacion no reintentaba, asi que la peticion se perdia sin mas aviso que un error generico.

## What Changes

- `authInterceptor` (frontend) reintenta una vez cualquier peticion a la API que el backend rechace con 401: fuerza una renovacion de sesion contra Supabase Auth y repite la peticion con el `access_token` nuevo.
- Si la renovacion de sesion tambien falla (p.ej. el refresh token ya no es valido: la sesion esta muerta de verdad, no solo caducada), el interceptor cierra la sesion local y redirige a login, propagando ademas el 401 original para que la pantalla en curso no quede en un estado inconsistente.
- `SupabaseService` incorpora un metodo `refreshSession()` que expone esa renovacion forzada.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `user-auth`: la sesion JWT de Supabase gana un comportamiento de reintento en el cliente cuando el backend rechaza el token por caducado, en vez de propagar el 401 a la primera.

## Impact

- `frontend/src/app/core/auth.interceptor.ts`
- `frontend/src/app/core/supabase.service.ts`
- `frontend/src/app/core/auth.interceptor.spec.ts`
- No afecta al backend (`app/deps.py` sigue devolviendo 401 igual que antes); el cambio es puramente del lado del cliente.
