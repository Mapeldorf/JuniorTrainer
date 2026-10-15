# Tasks

## 1. Guardrail en modo monitor

- [x] 1.1 En `infra/litellm/config.yaml`, anadir `on_flagged: "monitor"` al guardrail `lakera-guard` y actualizar el comentario para reflejar la decision. Verificar que el YAML sigue siendo valido (`docker compose config` sin errores).

## 2. Revertir los workarounds de esta sesion

- [x] 2.1 Revertir `agents/code/app/service.py`, `agents/web/app/service.py`, `agents/evaluator/app/service.py` y `agents/reviewer/app/service.py` a su estado anterior (prompts originales, sin el filtro `_is_selectable`). Verificar que no queda `_is_selectable` y que las frases defensivas vuelven a su redaccion original.

## 3. Verificacion

- [x] 3.1 Reconstruir/reiniciar el servicio `litellm` para que relea `config.yaml`, y enviar a traves del proxy una peticion que Lakera marca (contenido con la palabra `role`) usando la virtual key de un agente. Verificar que la respuesta es `200` (ya no `400 Violated guardrail policy`).
- [x] 3.2 Repetir la generacion de ejercicios con "Typescript" + repositorio (el caso que fallaba) y confirmar que llega a `ready` con candidatos.
- [x] 3.3 Confirmar que la deteccion se sigue registrando: en Langfuse, la traza muestra el span del guardrail `lakera-guard` con `flagged: true` aunque la llamada se complete (modo monitor, no bloqueo).
