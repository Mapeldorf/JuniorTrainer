# Design

## Context

Ver `proposal.md` para la motivacion y el hallazgo verificado (la UI ya esta reachable, `GET /ui` -> `307`). Investigacion hecha contra documentacion oficial de LiteLLM:

- `UI_USERNAME` (default `admin`) y `UI_PASSWORD` son variables de entorno que LiteLLM lee directamente, sin campo correspondiente en `config.yaml` -- mismo patron que `LAKERA_API_KEY`.
- Si `UI_PASSWORD` no esta puesta, la `master_key` del proxy funciona como contraseña de administrador para cualquiera que use el usuario por defecto.
- LiteLLM tambien soporta `disable_env_credential_login: true` (en `general_settings`) para desactivar el login con credenciales de entorno por completo, obligando a crear usuarios individuales (`proxy_admin`) desde la propia UI. La documentacion advierte explicitamente de un riesgo de bloqueo: activar ese flag antes de crear un usuario `proxy_admin` dejaria a cualquiera fuera de la UI hasta revertirlo con la master key.
- El puerto 4000 de `litellm` ya esta publicado al host (`docker-compose.yml`), necesario para el desarrollo y la verificacion manual que se ha hecho durante toda la serie de propuestas de LiteLLM en este proyecto.

## Goals / Non-Goals

**Goals:**
- Que la UI deje de aceptar la `master_key` compartida como contraseña de administrador.
- Cambio minimo: solo credenciales nuevas, sin tocar `config.yaml` ni introducir un flujo de usuarios individuales.

**Non-Goals:**
- No se activa `disable_env_credential_login`: dado el riesgo de bloqueo que la propia documentacion advierte, y que este proyecto tiene un unico mantenedor (no hace falta atribuir acciones a usuarios distintos), el beneficio no compensa la complejidad y el riesgo de quedarse fuera. Si en el futuro hubiera varios administradores, seria el momento de revisar esta decision.
- No se restringe el acceso de red al puerto 4000 (p. ej. quitarlo de `ports` y exigir un tunel o VPN): el puerto publicado al host es necesario para el desarrollo normal de este proyecto (todas las verificaciones manuales de las propuestas anteriores de LiteLLM se han hecho asi). Restringir el acceso de red seria una decision de despliegue para un entorno de produccion real, fuera de alcance de esta propuesta.
- No se configura SSO: la documentacion lo menciona pero no detalla su configuracion, y es una complejidad claramente desproporcionada para un proyecto de un unico mantenedor.

## Decisions

- **Variables con prefijo `LITELLM_UI_` en `.env`, mapeadas a `UI_USERNAME`/`UI_PASSWORD` (sin prefijo) en `docker-compose.yml`.** Mismo razonamiento que motivo la propuesta `fix-agent-model-env-collision`: nombrar la variable en `.env` igual que la que LiteLLM espera crea riesgo de colision si en el futuro otro servicio tuviera una variable con ese mismo nombre generico. Prefijarla en `.env` y traducirla explicitamente en el `environment:` del servicio `litellm` (igual que ya se hace con `DATABASE_URL`/`PRESIDIO_*`) evita repetir ese error.
- **Solo `UI_USERNAME`/`UI_PASSWORD`, sin `disable_env_credential_login`.** Ver Non-Goals: el riesgo de bloqueo documentado por LiteLLM no esta justificado para el beneficio (atribucion de acciones) que no aporta valor con un unico mantenedor.

## Risks / Trade-offs

- [La UI sigue siendo accesible desde el puerto 4000 publicado al host; cualquiera con red hasta ese puerto puede intentar el login, aunque ya no con la master key] → Mitigacion: el ataque de fuerza bruta contra `UI_PASSWORD` ya esta limitado por el rate limiting de login que LiteLLM trae por defecto (mas de 10 intentos fallidos desde una misma direccion en 60s bloquea esa direccion 5 minutos, segun su documentacion); se puede generar `LITELLM_UI_PASSWORD` con la misma robustez que el resto de credenciales del proyecto (`openssl rand -hex 32`).
- [Un unico usuario/contraseña compartido para la UI, sin atribucion de quien hizo cada cambio] → Mitigacion: aceptado en Non-Goals; es el mismo nivel de atribucion que ya existe para `LITELLM_MASTER_KEY` y para el resto de credenciales administrativas de este proyecto, no una regresion.
