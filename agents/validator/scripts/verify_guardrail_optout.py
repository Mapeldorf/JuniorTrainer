"""Verificacion manual del opt-out del guardarrail global en la virtual key
del agente validador (requisito "Exclusion del guardarrail global en la key
del validador" de `specs/litellm-agent-keys/spec.md`, change
`validacion-tecnologias-agente-juez`).

Por que hace falta esta verificacion. El guardarrail GLOBAL `lakera-guard`
(`default_on: true`) no solo detecta inyeccion: tambien ENMASCARA la PII que
encuentra. Si corriera en el validador, enmascararia el dato personal antes
de que `presidio-pii-block` pudiera verlo, y el validador NUNCA rechazaria
ese dato -- un control de seguridad desactivando a otro por el orden en que
se ejecutan. La virtual key del validador se excluye de ese guardarrail
global con la metadata `opted_out_global_guardrails: ["lakera-guard"]`.

Que se podia comprobar ya y que no. Que la metadata se aplica al crear la
key y se repara en re-ejecuciones se ve leyendo
`infra/litellm/provision_keys.py`. Lo que NO se comprobaba en ninguna parte
es el comportamiento que justifica el mecanismo: que, con la exclusion
puesta, un dato personal llegue SIN enmascarar a `presidio-pii-block` y este
rechace la llamada. Eso depende del orden de ejecucion interno de LiteLLM,
no de codigo propio, asi que solo se puede verificar ejecutandolo.

La eleccion de los vectores de prueba es la clave del diseno. El pre-filtro
determinista del propio agente (`app/input.py`) ya rechaza email, telefono,
IBAN y DNI/NIE ANTES de invocar al modelo, asi que esas entradas nunca
llegan al proxy y no sirven para probar el guardarrail. Las entidades que
Presidio cubre y el pre-filtro NO son `CREDIT_CARD` e `IP_ADDRESS`: una
tarjeta y una IP atraviesan el pre-filtro y su unica proteccion es el
guardarrail del proxy. Son, por tanto, los dos unicos vectores que aislan la
capa bajo prueba. La comprobacion 1 lo verifica explicitamente, para que
este script no se vuelva vacio en silencio si algun dia se anaden esos
patrones al pre-filtro.

El criterio de exito, y el modo de fallo que importa. La llamada SHALL
fallar con un error de guardarrail. Si el modelo RESPONDE -- con cualquier
veredicto -- significa que la PII llego al proveedor, enmascarada o no, y
que el opt-out no esta surtiendo efecto o `presidio-pii-block` no esta
vinculado al deployment. Un veredicto `valid=false` NO es un resultado
correcto aqui: es exactamente el sintoma del fallo que este script busca.

Comprueba:
  1. El pre-filtro determinista NO cubre tarjeta ni IP (sin red ni modelo),
     que es la precondicion que hace validos los vectores de 3 y 4.
  2. La virtual key del validador lleva la metadata de exclusion, y la de
     otro agente no la lleva (requiere LiteLLM y LITELLM_MASTER_KEY).
  3. Una tarjeta de credito en la entrada se RECHAZA en el guardarrail, sin
     que el modelo llegue a responder (requiere LiteLLM y Presidio).
  4. Una direccion IP en la entrada se rechaza igual (mismo motivo).

Los numeros usados son valores de prueba publicos (la tarjeta de prueba
4111 1111 1111 1111 y una IP de rango privado), no datos personales reales.

Uso (desde agents/validator/, con LiteLLM y Presidio corriendo y las
variables del .env de la raiz: AGENT_VALIDATOR_LITELLM_KEY, VALIDATOR_MODEL,
VALIDATOR_API_KEY y, para la comprobacion 2, LITELLM_MASTER_KEY):
    python -m scripts.verify_guardrail_optout

Ejecutandolo DESDE EL HOST (no dentro de la red de Docker) hay que apuntar el
proxy al puerto publicado, porque el valor por defecto de `litellm_base_url`
es el nombre de servicio de Docker y no resuelve fuera de ella:
    LITELLM_BASE_URL=http://localhost:4000/v1 python -m scripts.verify_guardrail_optout

Si el stack no esta accesible, el script termina con codigo 2 y el mensaje
"NO CONCLUYENTE": no se puede afirmar que el control funcione, pero tampoco
que este roto. Un fallo real de la verificacion sale como AssertionError.
"""

import asyncio
import logging
import os

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config import _REPO_ROOT_ENV, get_settings
from app.input import find_pii_like
from app.service import validate_technologies

logging.basicConfig(level=logging.INFO)

# Valores de prueba publicos, no datos reales: la tarjeta de prueba de Visa
# y una IP de rango privado (RFC 1918).
_TEST_CARD = "4111 1111 1111 1111"
_TEST_IP = "192.168.1.1"

# Entidades que Presidio cubre y el pre-filtro determinista no, con el
# guardarrail que debe atraparlas.
_VECTORS = ((_TEST_CARD, "CREDIT_CARD"), (_TEST_IP, "IP_ADDRESS"))

_GUARDRAIL_MARKERS = (
    "guardrail",
    "presidio",
    "pii",
    "blocked",
    "violated",
    "moderation",
)

_UNREACHABLE_MARKERS = (
    "connect",
    "connection",
    "refused",
    "getaddrinfo",
    "name or service not known",
    "timed out",
    "timeout",
)


class _AdminSettings(BaseSettings):
    """La master key NO esta en el `Settings` del agente a proposito: ningun
    agente debe poder administrar el proxy. Este script no es un agente, sino
    una comprobacion de administracion, y la lee del mismo `.env` de la raiz
    que el resto para que la comprobacion 2 no se omita por defecto -- una
    comprobacion que se omite es una comprobacion que nunca corre. El entorno
    real tiene prioridad sobre el fichero, como en `provision_keys.py`."""

    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV, extra="ignore")

    litellm_master_key: str = ""


class StackUnavailable(RuntimeError):
    """LiteLLM o Presidio no estan accesibles: no se puede concluir nada
    sobre el guardarrail. Distinto de "el control no funciona"."""


def _classify(exc: BaseException) -> str:
    """Clasifica el fallo de la llamada. Importa distinguir un bloqueo del
    guardarrail (lo que se busca) de un stack caido (no concluyente) y de
    cualquier otro error (hay que mirarlo a mano, no darlo por bueno)."""
    message = str(exc).lower()
    if any(marker in message for marker in _GUARDRAIL_MARKERS):
        return "blocked"
    if any(marker in message for marker in _UNREACHABLE_MARKERS):
        return "unreachable"
    return "unknown"


def check_prefilter_does_not_cover_card_and_ip() -> None:
    """Precondicion de las comprobaciones 3 y 4: si el pre-filtro empezara a
    cubrir tarjeta o IP, esas entradas se rechazarian antes de llegar al
    proxy y este script dejaria de probar el guardarrail sin avisar."""
    if find_pii_like([_TEST_CARD]):
        raise AssertionError(
            "el pre-filtro determinista ya rechaza la tarjeta de prueba: este script "
            "ya no prueba el guardarrail del proxy. Elige otro vector que Presidio "
            "cubra y el pre-filtro no, y actualiza _VECTORS"
        )
    if find_pii_like([_TEST_IP]):
        raise AssertionError(
            "el pre-filtro determinista ya rechaza la IP de prueba: ver el mensaje "
            "anterior, aplica lo mismo"
        )
    # Contraste: lo que el pre-filtro si cubre, para que un find_pii_like
    # roto (que devolviera siempre vacio) no haga pasar las dos asserts de
    # arriba por el motivo equivocado.
    if not find_pii_like(["12345678Z"]):
        raise AssertionError("find_pii_like no detecta un DNI: el pre-filtro esta roto")
    print("1. pre-filtro: OK (no cubre tarjeta ni IP, si cubre DNI -- vectores validos)")


def check_key_metadata() -> None:
    """La metadata de exclusion esta en la key del validador y solo en ella.
    Se consulta el estado real en LiteLLM, no la intencion del script de
    aprovisionamiento."""
    master_key = os.environ.get("LITELLM_MASTER_KEY") or _AdminSettings().litellm_master_key
    if not master_key:
        print(
            "2. metadata de la key: OMITIDA (falta LITELLM_MASTER_KEY, ni en el "
            "entorno ni en el .env de la raiz)"
        )
        return

    # La base de administracion es la del proxy sin el sufijo /v1 que usa el
    # cliente de modelos.
    admin_base = get_settings().litellm_base_url.rstrip("/").removesuffix("/v1")

    def _metadata(client: httpx.Client, alias: str) -> dict:
        response = client.get(
            "/key/list", params={"key_alias": alias, "return_full_object": "true"}
        )
        response.raise_for_status()
        keys = response.json()["keys"]
        if not keys:
            raise AssertionError(f"no existe ninguna virtual key con alias {alias!r}")
        return keys[0].get("metadata") or {}

    try:
        with httpx.Client(
            base_url=admin_base,
            headers={"Authorization": f"Bearer {master_key}"},
            timeout=30.0,
        ) as client:
            validator_metadata = _metadata(client, "agent-validator")
            evaluator_metadata = _metadata(client, "agent-evaluator")
    except httpx.HTTPStatusError as exc:
        # Un rechazo de credencial no es un stack caido: distinguirlo evita
        # dar por "no concluyente" lo que en realidad es una master key mal
        # puesta (p. ej. sin el prefijo `sk-` que espera LiteLLM).
        if exc.response.status_code in (401, 403):
            raise AssertionError(
                f"LiteLLM rechazo la master key ({exc.response.status_code}): no se "
                "puede comprobar la metadata de las keys. Revisa LITELLM_MASTER_KEY"
            ) from exc
        raise StackUnavailable(
            f"LiteLLM respondio {exc.response.status_code} en {admin_base}: {exc}"
        ) from exc
    except httpx.RequestError as exc:
        raise StackUnavailable(f"no se pudo consultar LiteLLM en {admin_base}: {exc}") from exc

    opted_out = validator_metadata.get("opted_out_global_guardrails")
    if opted_out != ["lakera-guard"]:
        raise AssertionError(
            "la key del validador no lleva la exclusion del guardarrail global: "
            f"opted_out_global_guardrails={opted_out!r}. Ejecuta "
            "infra/litellm/provision_keys.py para repararla"
        )
    if "opted_out_global_guardrails" in evaluator_metadata:
        raise AssertionError(
            "la key del evaluador lleva exclusion de guardarrailes globales, y no "
            f"deberia: metadata={evaluator_metadata!r}"
        )
    print("2. metadata de la key: OK (solo el validador esta excluido de lakera-guard)")


async def _check_vector_is_blocked(value: str, entity: str, number: int) -> None:
    try:
        result = await validate_technologies(["React", value], context="generation")
    except BaseException as exc:  # noqa: BLE001 -- se clasifica a continuacion
        kind = _classify(exc)
        if kind == "blocked":
            print(
                f"{number}. {entity}: OK (la llamada se rechazo en el guardarrail, "
                f"el modelo no respondio) -- {type(exc).__name__}: {exc}"
            )
            return
        if kind == "unreachable":
            raise StackUnavailable(
                f"{entity}: LiteLLM o Presidio no responden, no se puede concluir "
                f"nada sobre el guardarrail -- {type(exc).__name__}: {exc}"
            ) from exc
        raise AssertionError(
            f"{entity}: la llamada fallo con un error que no parece un bloqueo de "
            f"guardarrail ni un stack caido. Revisalo a mano antes de darlo por "
            f"bueno -- {type(exc).__name__}: {exc}"
        ) from exc

    # Sin excepcion: el modelo respondio, asi que la PII atraveso el proxy.
    # Da igual el veredicto; `valid=false` es el sintoma tipico de que
    # lakera-guard enmascaro el dato y presidio-pii-block no tuvo nada que
    # bloquear.
    raise AssertionError(
        f"{entity}: el modelo RESPONDIO (valid={result.valid}, reason={result.reason!r}) "
        "en vez de que la llamada se rechazara en el guardarrail. La PII llego al "
        "proveedor: o la key del validador no esta excluida del guardarrail global "
        "lakera-guard (que la enmascara antes de que presidio-pii-block la vea), o "
        "presidio-pii-block no esta vinculado al deployment del validador"
    )


async def check_guardrail_blocks_card() -> None:
    await _check_vector_is_blocked(_TEST_CARD, "CREDIT_CARD", 3)


async def check_guardrail_blocks_ip() -> None:
    await _check_vector_is_blocked(_TEST_IP, "IP_ADDRESS", 4)


def main() -> int:
    check_prefilter_does_not_cover_card_and_ip()
    try:
        check_key_metadata()
        asyncio.run(check_guardrail_blocks_card())
        asyncio.run(check_guardrail_blocks_ip())
    except StackUnavailable as exc:
        print(f"\nNO CONCLUYENTE: {exc}")
        print(
            "Levanta el stack (docker compose up litellm presidio-analyzer "
            "presidio-anonymizer) y vuelve a ejecutarlo."
        )
        return 2
    print("\nTodas las comprobaciones han pasado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
