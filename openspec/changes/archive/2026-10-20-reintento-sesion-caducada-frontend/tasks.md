# Tasks

## 1. Renovacion de sesion

- [x] 1.1 Anadir `refreshSession()` a `SupabaseService` y verificar que delega en `supabase.auth.refreshSession()`

## 2. Reintento y cierre de sesion en el interceptor

- [x] 2.1 En `authInterceptor`, capturar el 401 de una peticion con token y reintentarla una vez con el token renovado; verificar con el test "reintenta una vez con el token renovado si el backend responde 401"
- [x] 2.2 Si la renovacion de sesion tambien falla, cerrar sesion (`signOut()`), redirigir a `/login` y propagar el 401 original; verificar con el test "cierra sesion y manda a login si la renovacion tambien falla, propagando el 401"

## 3. Verificacion

- [x] 3.1 Ejecutar la suite completa del frontend (`ng test --watch=false`) y verificar que los 5 tests de `auth.interceptor.spec.ts` y el resto de la suite pasan sin regresiones
