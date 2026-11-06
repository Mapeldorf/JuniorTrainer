# Proposal

## Why

El agente validador aplica hoy una politica default-deny que solo reconoce como validas las "tecnologias de programacion claramente reconocibles" (lenguajes, frameworks, librerias, bases de datos, herramientas, plataformas). No contempla los conceptos, caracteristicas o temas propios de una tecnologia o lenguaje, asi que rechaza entradas como "Componentes en Angular" o "Guards en Angular" -- temas sobre los que tiene pleno sentido generar ejercicios de programacion, y que de hecho estan en el catalogo canonico (`public.technology`). Reproducido en vivo: una generacion con "Componentes en Angular" queda en error con el mensaje "las tecnologias no parecen tecnologias de programacion: ... es un concepto o tema dentro de un framework, no una tecnologia de programacion en si misma".

Ademas, el modelo del validador se invoca con la temperatura por defecto de `ChatOpenAI` (0.7). Al ser un criterio borderline, el mismo texto recibe veredictos contradictorios entre llamadas: "Componentes en Angular" fue aceptado al darlo de alta en el catalogo (contexto `catalog_entry`) y rechazado poco despues al validar una generacion (contexto `generation`), por el mismo agente. Un juez debe ser determinista.

## What Changes

- El criterio de validez del validador se amplia: una entrada es valida si es (a) una tecnologia de programacion, O (b) un concepto, caracteristica, modulo, API, patron o tema propio de una de esas tecnologias o lenguajes (por ejemplo "Componentes en Angular", "Hooks en React", "JOINs en SQL").
- Se mantiene la politica default-deny para todo lo demas: datos personales, identificadores, nombres de persona, frases o temas ajenos a la programacion, y texto sin sentido siguen dando veredicto negativo.
- El veredicto pasa a ser determinista: el modelo del validador se configura con temperatura cero, de modo que una misma entrada no reciba veredictos contradictorios entre llamadas (ni entre el alta en catalogo y la validacion de una generacion).
- El cambio afecta por igual a los dos contextos de llamada (`catalog_entry` y `generation`), porque ambos comparten el mismo criterio de "es un tema valido de programacion".

## Capabilities

### Modified Capabilities
- `technology-validation`: la nocion de "tecnologia de programacion claramente reconocible" se amplia para incluir los conceptos y temas propios de una tecnologia o lenguaje; y el veredicto del validador pasa a exigirse determinista para unas mismas entradas.

## Impact

- `agents/validator/app/service.py`: prompt de sistema mas amplio (acepta tecnologias y conceptos/temas propios de una tecnologia, con ejemplos) y wording coherente de los campos de respuesta. Ya implementado.
- `agents/validator/app/llm.py`: `temperature=0` en `build_validator_model`. Ya implementado.
- `openspec/specs/technology-validation/spec.md`: ampliar el criterio del requisito "Decision default-deny del validador" y de "Validacion de tecnologias como puerta previa a la generacion", y añadir la exigencia de determinismo del veredicto.
- `agents/validator/scripts/verify_validator.py`: cubrir que un concepto/tema propio de una tecnologia da `valid=True` y que lo no-tecnologico sigue dando `valid=False`.
- Sin cambios de esquema de base de datos, de contrato A2A ni del rol `agents_validator_reader`.
