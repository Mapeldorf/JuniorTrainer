# Spec Delta

## MODIFIED Requirements

### Requirement: Validacion de tecnologias como puerta previa a la generacion
El sistema SHALL validar, antes de invocar a los agentes de entrada (web, codigo y ejercicios), que las entradas introducidas son temas validos de programacion -- es decir, una tecnologia de programacion (lenguaje, framework, libreria, base de datos, herramienta o plataforma) o un concepto, caracteristica, modulo, API, patron o tema propio de una de esas tecnologias o lenguajes -- mediante un agente validador dedicado, y SHALL continuar con la generacion unicamente si el validador da un veredicto afirmativo. En este contexto, el validador SHALL comprobar unicamente que cada entrada es un tema valido de programacion, y SHALL NOT compararla contra el catalogo de tecnologias existentes ni rechazarla por coincidir con una tecnologia ya existente.

#### Scenario: Tecnologias validas
- **WHEN** se inicia una generacion cuyas entradas son todas tecnologias de programacion reconocibles
- **THEN** el validador da un veredicto afirmativo y la generacion continua con los agentes de entrada

#### Scenario: Concepto o tema propio de una tecnologia
- **WHEN** alguna de las entradas es un concepto, caracteristica o tema propio de una tecnologia o lenguaje de programacion (por ejemplo "Componentes en Angular", "Guards en Angular" o "Hooks en React")
- **THEN** el validador la considera un tema valido, da un veredicto afirmativo y la generacion continua con los agentes de entrada

#### Scenario: Entrada no relacionada con la programacion
- **WHEN** al menos una de las entradas introducidas no es una tecnologia de programacion ni un concepto o tema propio de una tecnologia de programacion
- **THEN** el validador rechaza la entrada, la generacion queda en estado de error y no se invoca a ningun agente de entrada

#### Scenario: Tecnologia ya existente en el catalogo
- **WHEN** se inicia una generacion con una tecnologia que ya esta en el catalogo con ese mismo nombre, o que el validador consideraria una variante semantica de una tecnologia ya existente
- **THEN** el validador no la rechaza por ese motivo, y la generacion continua si la entrada es un tema valido de programacion
- **AND** en este contexto el validador comprueba unicamente que cada entrada es un tema valido de programacion, sin compararla contra el catalogo de tecnologias existentes

### Requirement: Decision default-deny del validador
El validador SHALL dar un veredicto afirmativo unicamente cuando todas las entradas sean, con claridad, un tema valido de programacion: una tecnologia de programacion reconocible, o un concepto, caracteristica, modulo, API, patron o tema propio de una tecnologia o lenguaje de programacion. SHALL rechazar ante cualquier duda, ambiguedad, desconocimiento, dato personal, identificador, nombre de persona, frase o tema ajeno a la programacion, o texto que no pueda asociar con claridad a ninguna tecnologia o lenguaje de programacion. El veredicto del validador SHALL ser lo mas determinista posible para unas mismas entradas, de modo que una misma entrada no reciba veredictos contradictorios entre llamadas (por ejemplo, configurando la generacion del modelo con temperatura cero).

#### Scenario: Entrada clara
- **WHEN** las entradas introducidas son inequivocamente tecnologias de programacion
- **THEN** el validador da un veredicto afirmativo

#### Scenario: Concepto o tema propio de una tecnologia
- **WHEN** una entrada es un concepto, caracteristica o tema propio de una tecnologia o lenguaje de programacion (por ejemplo "Componentes en Angular")
- **THEN** el validador da un veredicto afirmativo

#### Scenario: Entrada ambigua, desconocida o ajena a la programacion
- **WHEN** alguna de las entradas es ambigua, desconocida, un dato personal, un nombre de persona, o un tema sin relacion con la programacion
- **THEN** el validador da un veredicto negativo

#### Scenario: Veredicto determinista entre llamadas
- **WHEN** una misma entrada se valida mas de una vez (por ejemplo, al darla de alta en el catalogo y despues al validar una generacion de ejercicios)
- **THEN** el validador da el mismo veredicto en ambas llamadas, sin contradecirse
