# litellm-admin-access Specification

## Purpose
Garantiza que la UI de administracion de LiteLLM (gestion de virtual keys, budgets y uso) autentica con una credencial propia, independiente de la `master_key` que usan los scripts de aprovisionamiento y las llamadas administrativas por API.

## Requirements

### Requirement: Credencial propia para el login de la UI
El sistema SHALL configurar la UI de administracion de LiteLLM con un usuario y contraseña propios (`UI_USERNAME`/`UI_PASSWORD`), y el login SHALL dejar de aceptar la `master_key` del proxy como contraseña valida una vez esa credencial propia este configurada.

#### Scenario: Login con la credencial propia
- **WHEN** alguien inicia sesion en `/ui` con el usuario y la contraseña configurados para la UI
- **THEN** el acceso se concede con normalidad

#### Scenario: La master key ya no sirve como contraseña de la UI
- **WHEN** alguien intenta iniciar sesion en `/ui` usando la `master_key` del proxy como contraseña
- **THEN** el sistema SHALL rechazar ese intento de acceso
