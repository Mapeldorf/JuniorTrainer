# Design

## Context

`agents/validator/app/service.py` construye un prompt de sistema con una politica default-deny ESTRICTA: solo da `valid=true` cuando todas las cadenas son "tecnologias de programacion claramente reconocibles", y enumera como validas unicamente lenguajes, frameworks, librerias, bases de datos, herramientas y plataformas. No menciona los conceptos o temas propios de una tecnologia (componentes, guards, hooks, directivas...), asi que el modelo los clasifica como "concepto, no tecnologia" y los rechaza.

El catalogo canonico (`public.technology`) contiene, sin embargo, 13 tecnologias de las cuales 5 son precisamente de ese tipo ("Componentes en Angular", "Guards en Angular", "Directivas estructurales en Angular", "RxJS en Angular", "HttpClient en Angular"): el tech lead las elige de un selector poblado desde ahi, de modo que llegan a la generacion y el validador las rechaza, dejando la generacion en error.

A esto se suma que `build_validator_model` (`agents/validator/app/llm.py`) no fija `temperature`, por lo que usa la de por defecto de `ChatOpenAI` (0.7). Con un criterio borderline y temperatura alta, el veredicto no es reproducible: la misma entrada ("Componentes en Angular") fue aceptada al darla de alta y rechazada al validar una generacion. Ver proposal.md - Why.

## Goals / Non-Goals

**Goals:**
- Que el validador acepte como validos los conceptos, caracteristicas y temas propios de una tecnologia o lenguaje de programacion, no solo las tecnologias "en si mismas".
- Que el veredicto sea determinista: una misma entrada recibe siempre el mismo veredicto, sin contradecirse entre el alta en catalogo y la validacion de generacion.
- Mantener intacta la politica default-deny para lo que no es programacion: datos personales, identificadores, nombres, frases y temas ajenos, texto sin sentido.

**Non-Goals:**
- No se toca el contrato A2A del validador (no se añaden campos ni skills nuevos).
- No se toca la comprobacion semantica de duplicados del contexto `catalog_entry` (sigue igual).
- No se cambia el esquema de base de datos, el catalogo ni el rol `agents_validator_reader`.
- No se limpia ni se reorganiza el catalogo de tecnologias: las entradas tipo tema se consideran validas, no un error a corregir.

## Decisions

### D1: Ampliar el criterio de validez en el prompt de sistema, con ejemplos
El `_BASE_SYSTEM_PROMPT` pasa a definir "tema valido" como (a) una tecnologia de programacion O (b) un concepto, caracteristica, modulo, API, patron o tema propio de una de esas tecnologias o lenguajes, con ejemplos explicitos ("Componentes en Angular", "Guards en Angular", "Hooks en React", "async/await en Python", "Generics en TypeScript", "JOINs en SQL"). El default-deny se conserva, pero formulado sobre el criterio ampliado: se rechaza lo que no se puede asociar con claridad a ninguna tecnologia o lenguaje de programacion. Como `catalog_entry` y `generation` comparten `_BASE_SYSTEM_PROMPT`, la ampliacion aplica a los dos contextos a la vez.

Alternativa descartada: limpiar el catalogo para que solo tenga nombres de tecnologia "canonicos" y dejar el prompt estricto. Se descarta porque los temas propios de una tecnologia son material legitimo -- y habitual -- para ejercicios de programacion; el problema es el criterio del juez, no los datos.

### D2: `temperature=0` en el modelo del validador
`build_validator_model` fija `temperature=0`. Es un juez, no un generador: su salida debe ser reproducible. Elimina la causa de los veredictos contradictorios observados entre llamadas para la misma entrada.

Alternativa descartada: cachear el veredicto por entrada. Se descarta por innecesaria y por introducir invalidacion y estado; la temperatura cero resuelve el problema en origen sin estado adicional.

## Risks / Trade-offs

- **[Riesgo] Un criterio mas amplio deja pasar entradas vagas** (p. ej. "cosas de Angular") que antes habria rechazado -> **Mitigacion**: el prompt exige poder asociar la entrada "con claridad" a una tecnologia o lenguaje, y mantiene el default-deny para lo ambiguo; se cubre con casos de `verify_validator.py` que incluyen entradas ambiguas y no-tecnologicas de control.
- **[Trade-off] temperature=0 no garantiza determinismo absoluto** (el proveedor puede no ser perfectamente determinista) -> se acepta: reduce drasticamente la varianza observada y es la practica estandar para un juez; el objetivo del spec es "lo mas determinista posible", no una garantia formal del proveedor.
- **[Riesgo] Desviacion respecto al spec vigente**: el requisito default-deny describia el criterio como "tecnologias de programacion"; esta propuesta lo amplia -> **Mitigacion**: es justamente lo que este change formaliza en el delta de `technology-validation`.

## Migration Plan

1. Cambios en `agents/validator/app/service.py` (prompt) y `llm.py` (temperature=0) -- ya implementados; recargados en caliente en desarrollo via volumen + `--reload`.
2. Ampliar `agents/validator/scripts/verify_validator.py` con casos de concepto/tema propio de una tecnologia (validos) y de control no-tecnologico (invalidos).
3. Validar y archivar el change, sincronizando `openspec/specs/technology-validation/spec.md`.
4. Rollback: revertir el prompt y la temperatura a sus valores anteriores; no hay cambios de datos ni de contrato que revertir.
