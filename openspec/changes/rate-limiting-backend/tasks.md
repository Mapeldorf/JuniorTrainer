# Tasks

## 1. Dependencia y configuracion base

- [x] 1.1 Añadir `slowapi` a `backend/requirements.txt` y verificar que `pip install -r requirements.txt` instala sin conflictos con `fastapi`/`httpx`/`a2a-sdk`.
- [x] 1.2 Crear `backend/app/rate_limit.py` con el `Limiter` (key function por `profile.id` via revalidacion de token), `default_limits` y las constantes de limite estricto para alta de alumnos e inicio de generaciones, y verificar que el modulo importa sin errores (`python -c "import app.rate_limit"`).

## 2. Integracion en la app

- [x] 2.1 Registrar `app.state.limiter`, el middleware de `slowapi` y el exception handler de `RateLimitExceeded` (cuerpo generico, sin detalles de configuracion) en `backend/app/main.py`, y verificar que el import check existente del CI (`python -c "from app.main import app"`) sigue pasando.

## 3. Limite estricto en alta de alumnos

- [x] 3.1 Decorar `invite_student` (`backend/app/routers/users.py`) con el limite estricto de `rate_limit.py`.

## 4. Limite estricto en inicio de generaciones

- [x] 4.1 Decorar `start_generation` (`backend/app/routers/generations.py`) con el limite estricto de `rate_limit.py`.

## 5. Verificacion manual

- [x] 5.1 Levantar el backend localmente (`uvicorn app.main:app`) y verificar manualmente con un cliente HTTP (curl/httpie) que una peticion normal a un endpoint autenticado responde igual que antes (sin el middleware de por medio). Verificado con `GET /health` (no decorado): peticiones normales devuelven 200 y, al superar el limite por defecto (30/minute), pasan a `429` con el cuerpo generico `{"detail": "Demasiadas peticiones, intentalo mas tarde"}`.
- [ ] 5.2 Verificar manualmente que una rafaga de peticiones a `POST /users` supera el limite estricto y recibe `429` con el cuerpo generico, y que no llega a invocarse la Admin API de Supabase. **Parcial**: se confirmo que la ruta decorada sigue exigiendo autenticacion (401 consistente en rafaga, el decorador no rompe el endpoint), pero no se pudo forzar el 429 real porque este entorno usa credenciales dummy de Supabase (sin token valido no se llega a pasar `require_tech_lead`, que corre antes que el limite). Pendiente de verificar con un entorno con Supabase real o un token de prueba valido.
- [ ] 5.3 Verificar manualmente que una rafaga de peticiones a `POST /generations` supera el limite estricto y recibe `429` con el cuerpo generico, sin que se cree fila en `generation`. **Parcial**: mismo caso que 5.2 -- 401 consistente en rafaga sin token valido, decorador no rompe la ruta, pero el 429 especifico de este endpoint no se ha podido forzar sin un token valido de Supabase.

Nota: este cambio no incluye tests automatizados (pytest) porque el backend no tiene infraestructura de test hoy; se cubrira en una propuesta aparte.
