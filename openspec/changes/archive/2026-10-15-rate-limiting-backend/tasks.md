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
- [x] 5.2 Verificar manualmente que una rafaga de peticiones a `POST /users` supera el limite estricto y recibe `429` con el cuerpo generico, y que no llega a invocarse la Admin API de Supabase. Verificado con `backend/scripts/verify_rate_limit.py` (harness ASGI con override de autenticacion y dobles de Supabase, porque este entorno usa credenciales dummy y el limite estricto corre tras la auth): la rafaga da `201, 201, 201, 429, 429` (limite estricto 3/minute), los 429 llevan el cuerpo generico `{"detail": "Demasiadas peticiones, intentalo mas tarde"}`, y la Admin API solo se invoca en las 3 peticiones que pasan (no en los 429).
- [x] 5.3 Verificar manualmente que una rafaga de peticiones a `POST /generations` supera el limite estricto y recibe `429` con el cuerpo generico, sin que se cree fila en `generation`. Verificado igual con `backend/scripts/verify_rate_limit.py`: la rafaga da `201` x5 y luego `429, 429` (limite estricto 5/minute) con el cuerpo generico, y el `insert` en `generation` solo se ejecuta 5 veces (no en los 429).

Nota: este cambio no incluye tests automatizados (pytest) porque el backend no tiene infraestructura de test hoy; se cubrira en una propuesta aparte.
