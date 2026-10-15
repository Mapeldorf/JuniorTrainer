# Design

## Context

El backend es un unico proceso FastAPI (`backend/app/main.py`) detras de uvicorn, sin balanceador ni Redis en la infraestructura actual (`docker-compose.yml`). Todas las rutas afectadas ya pasan por `Depends(get_current_profile)` / `require_tech_lead` (`app/deps.py`), que resuelve un `Profile` con `id` antes de llegar al handler. Ver `proposal.md` para el motivo.

## Goals / Non-Goals

**Goals:**
- Limitar peticiones por usuario autenticado (no solo por IP), reutilizando el `Profile` ya resuelto por las dependencies existentes.
- Que el limite por defecto cubra todo el API sin tener que anotar cada endpoint uno a uno.
- Que `POST /users` y `POST /generations` tengan limites mas estrictos y configurables de forma independiente.

**Non-Goals:**
- No se introduce Redis ni ningun almacen compartido entre procesos: con un unico proceso backend el almacenamiento en memoria de `slowapi` es suficiente. Si en el futuro se escala el backend a varias replicas, este diseño debe revisarse.
- No cubre rate limiting a nivel de infraestructura (proxy/CDN); es complementario, no sustituto.
- No cambia el modelo de autenticacion ni los roles.

## Decisions

- **Libreria: `slowapi`.** Es el wrapper de facto de `limits` para FastAPI/Starlette, se integra via middleware + decorador por ruta, y no obliga a Redis (usa `MemoryStorage` por defecto). Alternativa descartada: implementar un middleware propio con un diccionario en memoria -- mas codigo para reinventar edge cases (ventanas deslizantes, limpieza de contadores) que `slowapi`/`limits` ya resuelven.
- **Key function por `profile.id`, no por IP.** Todas las rutas afectadas exigen autenticacion antes de ejecutar el handler; usar el `id` del perfil evita que varios alumnos detras del mismo NAT/proxy compartan cuota, y evita que cambiar de IP sirva para esquivar el limite. Requiere una key function que lea el usuario ya autenticado: como `slowapi` saca la key de el `Request` de Starlette y no de las dependencies de FastAPI resueltas, la key function revalida el token igual que `get_current_profile` (llamada ligera, cacheable a nivel de `Limiter` por request) en lugar de depender del resultado de la dependency. Alternativa descartada: limitar por IP (`get_remote_address`) -- mas simple pero facil de esquivar y penaliza a usuarios legitimos detras de la misma IP.
- **Limite por defecto a nivel de app + decoradores especificos mas estrictos.** `Limiter` se registra como `app.state.limiter` con `default_limits = 30/minute` aplicado por el middleware de `slowapi` a todas las rutas; `invite_student` lleva ademas `3/minute` y `start_generation` lleva `5/minute`. Valores deliberadamente bajos: ningun uso legitimo (un tech lead invitando alumnos, iniciando generaciones) necesita mas de un puñado de estas acciones por minuto, y limites bajos reducen mas el margen de abuso (fuerza bruta, gasto de LLM) que limites holgados. Los valores concretos se documentan como constantes en el modulo de rate limiting, no hardcodeados en cada router, para poder ajustarlos sin tocar la spec.
- **Handler de `RateLimitExceeded` propio.** Se registra un exception handler que devuelve `429` con un cuerpo minimo (`{"detail": "Demasiadas peticiones, intentalo mas tarde"}`), para no depender del mensaje por defecto de `slowapi` y cumplir el requisito de no exponer detalles de configuracion.

## Risks / Trade-offs

- [Un unico proceso backend asume almacenamiento en memoria; si se despliega con varias replicas cada una lleva su propia cuenta, debilitando el limite real] -> Mitigacion: documentar la limitacion en el propio modulo de rate limiting; migrar a `RedisStorage` de `limits` si se escala horizontalmente.
- [Revalidar el token en la key function duplica una llamada a Supabase Auth por request] -> Mitigacion: el coste es el mismo que ya paga `get_current_profile`; no se introduce una llamada nueva de red critica, solo se reutiliza el mismo patron antes de que corra el handler.
- [Limites demasiado bajos podrian bloquear uso legitimo en picos] -> Mitigacion: valores iniciales conservadores y revisables sin cambiar el contrato de API (son constantes de configuracion, no parte de la spec).
