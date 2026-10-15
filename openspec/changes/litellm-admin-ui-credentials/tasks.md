# Tasks

## 1. Credenciales

- [x] 1.1 Añadir `LITELLM_UI_USERNAME` y `LITELLM_UI_PASSWORD` a `.env.example` (sin valor, con nota de generar la contraseña con `openssl rand -hex 32`, mismo estilo que el resto de `.env.example`). Tambien se actualizo el comentario de `LITELLM_MASTER_KEY` (decia "o la UI de LiteLLM", ya desactualizado con esta propuesta).
- [x] 1.2 Generar los valores reales en el `.env` local (usuario propio, p. ej. `admin`, y una contraseña generada con `openssl rand -hex 32`, distinta de `LITELLM_MASTER_KEY`). Verificado.

## 2. Configuracion en docker-compose

- [x] 2.1 En `docker-compose.yml`, añadir `UI_USERNAME: ${LITELLM_UI_USERNAME}` y `UI_PASSWORD: ${LITELLM_UI_PASSWORD}` al bloque `environment` del servicio `litellm`. Verificar que el YAML sigue siendo valido. Verificado.
- [x] 2.2 Recrear `litellm` (`docker compose up -d --force-recreate litellm`, recordando que variables nuevas no se recogen con `restart`) y confirmar en los logs que arranca sin error. Verificado.

## 3. Verificacion del login

- [x] 3.1 Confirmar que la `master_key` ya NO sirve como contraseña de la UI: intentar login en `/ui` con usuario `admin` y la `LITELLM_MASTER_KEY` como contraseña, y verificar que se rechaza. Verificado en el navegador: "Invalid credentials used to access UI. Check 'UI_USERNAME' and 'UI_PASSWORD'...".
- [x] 3.2 Confirmar que el login funciona con las credenciales nuevas: iniciar sesion en `/ui` con `LITELLM_UI_USERNAME`/`LITELLM_UI_PASSWORD` y verificar que se accede con normalidad (p. ej. comprobar que la pantalla de Virtual Keys lista las 5 keys ya existentes). Verificado: login correcto, dashboard carga (120 peticiones totales, coincide con la verificacion de esta sesion), pantalla de Virtual Keys lista las 5 keys con sus budgets y modelos restringidos.
- [x] 3.3 Confirmar que las llamadas administrativas por API (p. ej. `infra/litellm/provision_keys.py`, que sigue usando `LITELLM_MASTER_KEY` via `Authorization: Bearer`) siguen funcionando con normalidad -- esta propuesta solo cambia el login de la UI, no la autenticacion de la API. Verificado: el script funciona igual que siempre (las 5 keys reportadas "completa, omitida").
