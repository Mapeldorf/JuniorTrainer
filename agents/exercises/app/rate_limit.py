"""Rate limiting del agente (change resiliencia-agentes).

A diferencia del backend (`backend/app/rate_limit.py`), este agente no
tiene ningun usuario final que distinguir: su unico llamador legitimo es
el backend, identificado por la credencial de servicio compartida
(`app/service_auth.py`), no por un `profile.id` individual. Limitar por
IP (`get_remote_address`) es aqui el equivalente correcto -- en uso
normal, toda peticion legitima llega desde la misma IP (el contenedor del
backend), asi que el limite actua de facto como un limite global por
agente; en el escenario que motiva este requisito (autenticacion
comprometida, o un bug que dispare un bucle de llamadas), sigue acotando
el dano con independencia de si la credencial es valida.

`60/minute`: cubre con holgura una clase con decenas de alumnos
enviando respuestas en el mismo minuto, sin dejar de acotar un bucle de
reintentos descontrolado. Ver design.md del change.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

DEFAULT_LIMIT = "60/minute"

limiter = Limiter(key_func=get_remote_address, default_limits=[DEFAULT_LIMIT])
