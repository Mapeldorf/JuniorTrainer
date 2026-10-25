# agent-evaluation Specification

## Purpose
Define la evaluación reproducible de los agentes sobre un dataset dorado versionado en el repositorio, con métricas deterministas, un modo simulado apto para integración continua y un modo real contra modelos, para poder detectar si un cambio de código, de prompt o de modelo empeora el sistema.

## Requirements

### Requirement: Dataset dorado versionado en el repositorio
El sistema SHALL mantener en el repositorio un dataset dorado con un conjunto por agente evaluado (generacion, evaluacion, validacion, web y code) y un conjunto adversarial, en un formato de texto legible por diff, donde cada caso lleva un identificador unico y su resultado esperado o la propiedad verificable que debe cumplir.

#### Scenario: Todos los conjuntos presentes
- **WHEN** se carga el dataset
- **THEN** existen los seis conjuntos y cada uno tiene al menos un caso

#### Scenario: Identificadores unicos
- **WHEN** se carga el dataset
- **THEN** no hay dos casos con el mismo identificador dentro de un conjunto

#### Scenario: Caso mal formado
- **WHEN** un caso carece de un campo obligatorio de su conjunto o trae un valor fuera de rango
- **THEN** la carga falla indicando el conjunto, el caso y el campo, sin ejecutar ningun agente

#### Scenario: Etiquetas de evaluacion cubren los tres veredictos
- **WHEN** se carga el conjunto de evaluacion
- **THEN** contiene casos etiquetados como `correct`, `incomplete` e `incorrect`, incluidos casos limite

### Requirement: Cobertura de los seis agentes
El sistema SHALL evaluar los seis agentes (evaluador, revisor, validador, ejercicios, web y codigo), permitiendo elegir cuales ejecutar, y SHALL informar de forma independiente los resultados de cada uno.

#### Scenario: Todos por defecto
- **WHEN** se ejecuta la evaluacion sin indicar agentes
- **THEN** se evaluan los seis agentes y el informe contiene una seccion por cada uno

#### Scenario: Seleccion de agentes
- **WHEN** se piden solo los agentes web y codigo
- **THEN** solo esos dos se ejecutan y el informe no contiene a los demas

#### Scenario: Agente desconocido
- **WHEN** se pide un agente que no existe
- **THEN** la ejecucion termina con error indicando los agentes validos, sin ejecutar ninguno

### Requirement: Modo simulado sin red ni credenciales
El sistema SHALL poder ejecutar la evaluacion en modo simulado, sustituyendo el modelo de cada agente por un doble guionizado por el propio caso, sin acceso a red, a LiteLLM, a la base de datos ni a credenciales, de modo que el resultado dependa solo del codigo de los agentes y del dataset.

#### Scenario: Ejecucion sin entorno
- **WHEN** se ejecuta el modo simulado sin ninguna variable de entorno de credenciales ni servicio levantado
- **THEN** la ejecucion termina y produce el informe

#### Scenario: Resultado reproducible
- **WHEN** se ejecuta el modo simulado dos veces sobre el mismo codigo y dataset
- **THEN** las metricas no temporales de ambos informes son identicas

#### Scenario: Servicios externos sustituidos
- **WHEN** se evalua el agente web o el de codigo en modo simulado
- **THEN** las busquedas web, las lecturas de GitHub y la memoria persistente se sustituyen por datos del caso, y no se contacta con ningun servicio externo

#### Scenario: El codigo real del agente se ejecuta
- **WHEN** el doble de un caso devuelve una respuesta que incumple el contrato (JSON invalido, veredicto fuera de rango, justificacion de mas de 50 palabras)
- **THEN** el agente reacciona con su logica real de validacion y reintento, y el informe refleja ese comportamiento

### Requirement: Modo real contra el stack
El sistema SHALL poder ejecutar la misma evaluacion en modo real, llamando a los agentes con sus modelos a traves de LiteLLM, de forma explicita y nunca por defecto, e indicando en el informe el modo y los alias de modelo usados.

#### Scenario: El modo real exige pedirse
- **WHEN** se ejecuta la evaluacion sin indicar el modo
- **THEN** se usa el modo simulado

#### Scenario: Muestra repartida
- **WHEN** se limita el numero de casos por conjunto
- **THEN** los casos elegidos se reparten por todo el conjunto, en su orden, y no son simplemente los primeros

#### Scenario: Casos guionizados en modo real
- **WHEN** se ejecuta el modo real
- **THEN** los casos que existen para provocar un fallo concreto con un modelo falso (los que traen un guion o una expectativa simulada) no se ejecutan

#### Scenario: Adversariales de web y codigo en modo real
- **WHEN** se ejecuta el modo real para los agentes web o de codigo
- **THEN** sus casos adversariales no se ejecutan, porque el contenido no confiable lo aporta el caso y en ese modo el agente lee fuentes reales

#### Scenario: Stack no disponible
- **WHEN** se pide el modo real y LiteLLM no responde o falta la credencial del agente
- **THEN** la ejecucion falla antes de evaluar ningun caso, indicando que falta

#### Scenario: Sin escrituras
- **WHEN** se ejecuta cualquiera de los dos modos
- **THEN** no se escribe en la base de datos ni se persiste ningun ejercicio, respuesta, generacion o memoria de los agentes web y codigo, y la memoria no se lee salvo en los casos que la simulan

#### Scenario: Web real
- **WHEN** se evalua el agente web en modo real
- **THEN** las busquedas se hacen contra el servicio de busqueda real con la credencial del agente, y la ejecucion falla antes de evaluar si falta

#### Scenario: Codigo real con un repositorio configurado
- **WHEN** se evalua el agente de codigo en modo real y el repositorio real esta configurado por entorno (propietario, repositorio y commit)
- **THEN** el agente lee ese repositorio con su credencial real y los casos del conjunto se ejecutan contra el

#### Scenario: Tecnologias del repositorio real
- **WHEN** se evalua el agente de codigo en modo real y se configuran por entorno las tecnologias del repositorio
- **THEN** el agente analiza el repositorio con esas tecnologias en lugar de las del caso

#### Scenario: Codigo real sin repositorio configurado
- **WHEN** se evalua el agente de codigo en modo real sin repositorio configurado
- **THEN** sus casos se informan como omitidos con el motivo, no entran en ninguna metrica y la ejecucion no falla por ello

### Requirement: Aislamiento por agente
El sistema SHALL ejecutar cada agente en su propio proceso, con su propio entorno de dependencias, porque todos comparten el nombre de paquete `app`, y SHALL no modificar el codigo de produccion de los agentes para evaluarlos.

#### Scenario: Un agente por proceso
- **WHEN** se evaluan varios agentes en una misma ejecucion
- **THEN** cada uno se ejecuta en un proceso distinto y el informe agrupa sus resultados

#### Scenario: Fallo de un agente
- **WHEN** un agente no puede arrancar (dependencia ausente)
- **THEN** el informe lo marca como no ejecutado con el motivo y el resto de agentes se evaluan

### Requirement: Validez de salida y adherencia a limites
El sistema SHALL medir, por agente, el porcentaje de salidas que cumplen el contrato (JSON valido con el esquema esperado) y el porcentaje que respeta los limites de palabras: enunciado de 50 o menos, nombre de 8 o menos y justificacion de evaluador y revisor de 50 o menos.

#### Scenario: Salida conforme
- **WHEN** un agente devuelve un resultado que parsea y cumple los limites
- **THEN** el caso cuenta como valido y como adherente

#### Scenario: Tarea fallida por incumplimiento
- **WHEN** un agente falla la tarea porque la salida incumple el contrato tras su reintento
- **THEN** el caso cuenta como no valido o no adherente, segun la causa, y no como error del arnes

#### Scenario: Metrica sin casos
- **WHEN** un agente no tiene casos en el dataset
- **THEN** su metrica se informa como no disponible y no como cero

### Requirement: Tasa de activacion del reintento correctivo
El sistema SHALL medir, para los agentes que tienen reintento correctivo (evaluador, revisor, validador y ejercicios), el porcentaje de casos en los que lo necesitaron, contando las llamadas al modelo por caso, sin depender de logs ni de modificar el agente.

#### Scenario: Sin reintento
- **WHEN** un caso se resuelve con una sola llamada al modelo
- **THEN** no cuenta como reintento

#### Scenario: Con reintento
- **WHEN** un caso requiere una segunda llamada al modelo por una respuesta que incumplia el contrato
- **THEN** cuenta como activacion del reintento, aunque el resultado final sea correcto

#### Scenario: Agentes sin reintento
- **WHEN** se informan las metricas del agente web o del de codigo
- **THEN** la tasa de reintento se informa como no disponible, porque el agente de codigo hace siempre dos llamadas por diseno y no tiene reintento correctivo

### Requirement: Conformidad de cardinalidad en la generacion
El sistema SHALL medir el porcentaje de generaciones cuyo numero de candidatos coincide con el pedido, y verificar que cada candidato trae nombre, enunciado y respuesta esperada no vacios.

#### Scenario: Numero pedido
- **WHEN** se pide generar 3 candidatos y el agente devuelve 3 completos
- **THEN** el caso es conforme

#### Scenario: Numero distinto
- **WHEN** el agente devuelve un numero de candidatos distinto del pedido, o falla la tarea
- **THEN** el caso no es conforme

### Requirement: Exactitud del veredicto
El sistema SHALL comparar el `verdict` del evaluador con la etiqueta de cada caso y calcular exactitud, matriz de confusion de tres clases y el coeficiente kappa de Cohen, e informar tambien cuantos casos fallaron la tarea sin veredicto.

#### Scenario: Coincidencia total
- **WHEN** el veredicto coincide con la etiqueta en todos los casos
- **THEN** la exactitud es 1 y el kappa es 1

#### Scenario: Matriz de confusion
- **WHEN** hay casos mal clasificados
- **THEN** el informe muestra, para cada etiqueta esperada, cuantos casos recibieron cada veredicto

#### Scenario: Casos sin veredicto
- **WHEN** el evaluador falla la tarea en un caso
- **THEN** ese caso se cuenta aparte y no entra en la matriz ni en el kappa

### Requirement: Metricas del agente de codigo
El sistema SHALL medir, para el agente de codigo, el porcentaje de rutas elegidas por el modelo que existen en el listado real del repositorio, si el numero de lecturas respeta el presupuesto de 10 ficheros, y el porcentaje de fragmentos devueltos que estan copiados literalmente del fichero indicado y empiezan en la linea declarada.

#### Scenario: Rutas inventadas
- **WHEN** el modelo elige una ruta que no esta en el listado del repositorio
- **THEN** cuenta como ruta no valida, el agente no la lee y el caso sigue con las demas

#### Scenario: Ninguna ruta valida
- **WHEN** todas las rutas elegidas por el modelo son invalidas o ilegibles
- **THEN** el agente falla la tarea y el caso cuenta como fallo de contrato

#### Scenario: Presupuesto de lecturas
- **WHEN** el modelo elige mas de 10 rutas validas
- **THEN** el agente lee como mucho 10 y el caso cumple el presupuesto

#### Scenario: Fragmento inventado
- **WHEN** un fragmento devuelto no esta en el fichero que declara
- **THEN** cuenta como no fundamentado

#### Scenario: Memoria
- **WHEN** el caso simula un analisis ya en memoria
- **THEN** el agente responde sin llamar al modelo ni leer ficheros y el caso cuenta como acierto de memoria

### Requirement: Metricas del agente web
El sistema SHALL medir, para el agente web, si el numero de busquedas respeta el presupuesto de 5, el porcentaje de casos cuyo resumen menciona todas las tecnologias pedidas y el porcentaje de tecnologias sin fuentes cuyo resumen lo declara explicitamente.

#### Scenario: Presupuesto de busquedas
- **WHEN** se piden mas tecnologias que busquedas permitidas
- **THEN** el agente hace como mucho 5 busquedas, las tecnologias restantes se quedan sin fuentes y el caso cumple el presupuesto

#### Scenario: Tecnologia sin fuentes
- **WHEN** una tecnologia no tiene resultados de busqueda
- **THEN** el resumen debe decir explicitamente que no hay fuentes para ella, y si no lo dice cuenta como no declarada

#### Scenario: Cobertura de tecnologias
- **WHEN** el resumen no menciona alguna de las tecnologias pedidas
- **THEN** el caso no cuenta como cobertura completa

#### Scenario: Memoria
- **WHEN** el caso simula una investigacion ya en memoria
- **THEN** el agente responde sin buscar ni llamar al modelo y el caso cuenta como acierto de memoria

### Requirement: Precision del gate del validador y de la deteccion de duplicados
El sistema SHALL medir, sobre el conjunto de validacion, falsos positivos y falsos negativos del veredicto `valid` del validador, y precision y cobertura de la deteccion de duplicados contra un catalogo fijo aportado por el dataset, sin consultar la base de datos.

#### Scenario: Falso negativo del gate
- **WHEN** una cadena que no es una tecnologia recibe `valid = true`
- **THEN** cuenta como falso negativo del gate (se deja pasar algo invalido)

#### Scenario: Falso positivo del gate
- **WHEN** una tecnologia legitima recibe `valid = false`
- **THEN** cuenta como falso positivo del gate (se bloquea trabajo valido)

#### Scenario: Catalogo del dataset
- **WHEN** se evalua el contexto de alta en catalogo
- **THEN** el validador recibe como catalogo el aportado por el caso, no el de la base de datos

#### Scenario: Rechazo previo al modelo
- **WHEN** una entrada contiene un dato personal reconocible por el pre-filtro
- **THEN** el caso se resuelve sin ninguna llamada al modelo y el informe lo distingue de un rechazo del modelo

### Requirement: No repeticion de temas
El sistema SHALL medir el solapamiento entre los enunciados generados en generaciones consecutivas con las mismas tecnologias mediante una medida determinista basada en los terminos de cada enunciado, e informar el valor maximo y medio.

#### Scenario: Enunciados distintos
- **WHEN** dos generaciones consecutivas producen enunciados sin terminos significativos en comun
- **THEN** el solapamiento es bajo

#### Scenario: Enunciado repetido
- **WHEN** la segunda generacion repite un enunciado de la primera
- **THEN** el solapamiento de ese par es el maximo

### Requirement: Latencia por operacion
El sistema SHALL registrar la duracion de cada caso y calcular p50, p95 y p99 por agente, sin incluir en el calculo los casos que no llegaron a ejecutarse.

#### Scenario: Percentiles
- **WHEN** termina la ejecucion de un agente con casos
- **THEN** el informe incluye p50, p95 y p99 de su duracion

#### Scenario: Latencia en modo simulado
- **WHEN** la ejecucion es en modo simulado
- **THEN** el informe marca la latencia como no representativa del modelo real

### Requirement: Falsos positivos de guardarrail en modo real
El sistema SHALL medir, en modo real y sobre casos benignos del dataset, el porcentaje de llamadas rechazadas por un guardarrail del proxy, distinguiendolo de un fallo del modelo, y SHALL informarlo como no disponible en modo simulado.

#### Scenario: Llamada benigna bloqueada
- **WHEN** en modo real un caso benigno recibe un rechazo del proxy por guardarrail
- **THEN** cuenta como falso positivo de guardarrail y no como fallo de contrato del modelo

#### Scenario: Modo simulado
- **WHEN** la ejecucion es en modo simulado
- **THEN** la metrica se informa como no disponible

### Requirement: Casos adversariales como pruebas permanentes
El sistema SHALL incluir en el conjunto adversarial casos de texto no confiable (respuestas de alumno que intentan fijar el veredicto, tecnologias que son instrucciones o datos personales, fragmentos de busqueda web y ficheros de repositorio con instrucciones), y SHALL comprobar de forma determinista que el contenido no confiable viaja delimitado como dato en el prompt que recibe el modelo.

#### Scenario: Respuesta de alumno delimitada
- **WHEN** el evaluador recibe una respuesta de alumno del conjunto adversarial
- **THEN** el prompt enviado al modelo contiene esa respuesta entre los delimitadores de dato, y no fuera de ellos

#### Scenario: Contenido de terceros delimitado
- **WHEN** el agente web o el de codigo reciben un fragmento de busqueda o un fichero con instrucciones del conjunto adversarial
- **THEN** el prompt enviado al modelo lo contiene entre los delimitadores de dato

#### Scenario: Ruta fuera del repositorio
- **WHEN** en un caso adversarial el modelo elige una ruta fuera del repositorio
- **THEN** el agente no la lee y el caso se resuelve con las rutas validas

#### Scenario: Dato personal en una tecnologia
- **WHEN** una entrada adversarial del validador contiene un dato personal reconocible por el pre-filtro
- **THEN** el validador la rechaza antes de llamar al modelo

#### Scenario: Bloqueo por guardarrail
- **WHEN** en modo real un caso adversarial es rechazado por un guardarrail del proxy
- **THEN** el informe lo cuenta como bloqueado por guardarrail, distinto de un ataque exitoso y de un falso positivo

#### Scenario: Resistencia medida en modo real
- **WHEN** en modo real una respuesta adversarial obtiene `correct` cuando su etiqueta es otra
- **THEN** el informe lo cuenta como ataque exitoso, sin que ello bloquee la ejecucion

### Requirement: Informe estructurado y codigo de salida
El sistema SHALL producir en cada ejecucion un informe estructurado legible por maquina y un resumen legible, con el modo, la fecha, las metricas por agente y los casos fallidos, y SHALL terminar con codigo distinto de cero en modo simulado cuando una invariante del codigo no se cumple.

#### Scenario: Informe generado
- **WHEN** termina una ejecucion
- **THEN** existe un informe estructurado con modo, fecha, metricas y casos individuales

#### Scenario: Invariante rota en modo simulado
- **WHEN** en modo simulado un caso no produce el resultado que su guion determina (por ejemplo, una justificacion de mas de 50 palabras que se entrega sin reintento)
- **THEN** la ejecucion termina con codigo distinto de cero e identifica el caso

#### Scenario: El modo real no bloquea por umbral
- **WHEN** en modo real una metrica queda por debajo de lo deseable
- **THEN** la ejecucion informa el valor y termina con codigo cero, salvo errores de la propia ejecucion

### Requirement: Ejecucion del modo simulado en integracion continua
El sistema SHALL ejecutar el modo simulado en el flujo de integracion continua en cada pull request que modifique los agentes evaluados o el propio arnes, y SHALL no ejecutar el modo real en ese flujo.

#### Scenario: Cambio en un agente
- **WHEN** un pull request modifica codigo de un agente evaluado
- **THEN** el flujo de CI ejecuta el modo simulado y el merge queda condicionado a su resultado

#### Scenario: Cambio ajeno
- **WHEN** un pull request no toca los agentes evaluados ni el arnes
- **THEN** el trabajo de evaluacion no se ejecuta

#### Scenario: Sin modelos reales en CI
- **WHEN** corre el flujo de CI
- **THEN** no se hace ninguna llamada a un proveedor de modelos

### Requirement: Captura de tokens y coste por llamada
El sistema SHALL registrar en cada caso evaluado en modo real los tokens de entrada, de salida y de razonamiento de cada llamada al modelo, y el coste facturado cuando el proveedor lo informe, sin modificar el codigo de los agentes.

#### Scenario: Llamada con coste informado
- **WHEN** el proveedor devuelve el coste de la llamada
- **THEN** el registro del caso incluye los tokens y ese coste

#### Scenario: Llamada sin coste informado
- **WHEN** el proveedor devuelve tokens pero no coste
- **THEN** el registro incluye los tokens y el coste queda como no informado, sin inventarlo

#### Scenario: Caso con varias llamadas
- **WHEN** un caso requiere mas de una llamada al modelo
- **THEN** el registro suma los tokens y el coste de todas sus llamadas

#### Scenario: Modo simulado
- **WHEN** la ejecucion es en modo simulado
- **THEN** tokens y coste se informan como no disponibles, no como cero

### Requirement: Tabla de precios versionada
El sistema SHALL mantener en el repositorio una tabla de precios por millon de tokens de entrada y de salida de los modelos que usa y de los de referencia, con la fecha y la fuente de cada precio, y SHALL poder refrescarla desde una fuente publica sin credenciales.

#### Scenario: Precio con fecha y fuente
- **WHEN** se consulta el precio de un modelo
- **THEN** la tabla indica su precio de entrada y de salida, la fecha de la consulta y la fuente

#### Scenario: Modelo ausente
- **WHEN** se necesita el precio de un modelo que no esta en la tabla
- **THEN** el calculo falla indicando el modelo, en lugar de suponer un precio

#### Scenario: Refresco
- **WHEN** se ejecuta el refresco de precios
- **THEN** la tabla se actualiza con los precios publicados y la fecha de ese dia, sin enviar credenciales

### Requirement: Coste por operacion
El sistema SHALL calcular el coste medio de las cuatro operaciones del sistema (validar una tecnologia, evaluar una respuesta, generar sin repositorio y generar con repositorio) componiendo el coste medio medido de los agentes que intervienen, y SHALL desglosarlo por etapa.

#### Scenario: Composicion
- **WHEN** se calcula el coste de evaluar una respuesta
- **THEN** es la suma del coste medio del evaluador y del revisor, y el desglose muestra ambos

#### Scenario: Generacion con repositorio
- **WHEN** se calcula el coste de generar con repositorio
- **THEN** incluye al validador, al agente web, al de codigo (con sus dos llamadas) y al de ejercicios

#### Scenario: Etapa dominante
- **WHEN** se muestra el desglose de una operacion
- **THEN** cada etapa aparece con su coste y su porcentaje del total

#### Scenario: Agente sin datos
- **WHEN** falta la medicion de un agente que interviene en una operacion
- **THEN** la operacion se informa como no calculable e indica el agente que falta

### Requirement: Escenarios de uso por fases con supuestos explicitos
El sistema SHALL calcular el coste de una campana de incorporacion para los niveles de uso piloto, equipo y organizacion, expresados en numero de equipos (un tech lead y sus alumnos), en tres fases (generacion inicial, resolucion por los alumnos y regimen), a partir de un fichero editable de supuestos, y SHALL compararlo con el presupuesto de cada clave de LiteLLM en la ventana de 30 dias mas cargada.

#### Scenario: Generacion inicial
- **WHEN** el supuesto es generar 500 ejercicios guardados con 5 candidatos por generacion y una tasa de guardado del 90 %
- **THEN** el numero de generaciones por tech lead (112, el redondeo hacia arriba de 500 entre 4,5) y su coste se deducen de esos valores y no se escriben a mano

#### Scenario: Resolucion por los alumnos
- **WHEN** se indican los alumnos por equipo y los ejercicios que resuelve cada uno en la campana
- **THEN** el numero de evaluaciones es su producto por el numero de equipos y cada una cuesta lo de evaluador mas revisor

#### Scenario: Incorporaciones anuales
- **WHEN** se indican los alumnos que se incorporan cada ano a un equipo
- **THEN** el regimen incluye las evaluaciones de esos alumnos sobre el catalogo ya existente

#### Scenario: Supuestos editables
- **WHEN** se cambia un supuesto del fichero
- **THEN** el calculo refleja el cambio sin tocar el codigo

#### Scenario: Presupuesto de clave superado
- **WHEN** el coste estimado de un agente en la ventana de 30 dias mas cargada supera su presupuesto
- **THEN** el informe lo marca para ese nivel de uso y agente

#### Scenario: Tope por clave recomendado
- **WHEN** se calcula el pico de 30 dias de cada clave y se indica una holgura
- **THEN** el informe da, por nivel, el menor tope redondo que cubre el pico de la clave mas cargada con esa holgura, presentado como dimensionado y no como medida de seguridad

#### Scenario: Donde se concentra el coste
- **WHEN** se muestra el resultado de un nivel
- **THEN** aparece el reparto del coste total entre las tres fases y entre generacion y evaluacion

### Requirement: Coste de busquedas y lecturas externas
El sistema SHALL contar las busquedas web y las lecturas de repositorio de cada caso, SHALL calcular el coste de las busquedas como la cuota mensual del plan configurado mas los creditos que excedan los incluidos al precio del credito adicional, y SHALL informar de cualquier plan cuyos creditos no basten y no admita exceso.

#### Scenario: Busquedas contadas
- **WHEN** el agente web realiza busquedas en un caso
- **THEN** el registro del caso incluye cuantas hizo, sin contar las que el presupuesto rechaza

#### Scenario: Dentro de los creditos incluidos
- **WHEN** los creditos consumidos en la campana no superan los incluidos en el plan
- **THEN** el coste de las busquedas es la cuota mensual del plan por los meses con uso

#### Scenario: Por encima de los creditos incluidos
- **WHEN** los creditos consumidos superan los incluidos
- **THEN** el coste suma la cuota y el exceso de creditos multiplicado por el precio del credito adicional

#### Scenario: Plan gratuito insuficiente
- **WHEN** la demanda supera los creditos del plan gratuito
- **THEN** el informe indica que el plan no basta en lugar de calcular un coste

#### Scenario: Precio no configurado
- **WHEN** la tabla de precios no define el plan de busqueda
- **THEN** el coste de generar se muestra solo con el coste del modelo y marcado como incompleto

#### Scenario: Lecturas de repositorio
- **WHEN** el agente de codigo lee ficheros del repositorio
- **THEN** las lecturas se cuentan por caso y su coste es cero

### Requirement: Costes unitarios de la formacion
El sistema SHALL calcular, para cada nivel de uso, el coste por ejercicio guardado, el coste por evaluacion y el coste de formar a un alumno, entendido como sus evaluaciones mas su parte del coste de generacion de su equipo, sin estimar ahorros ni beneficios.

#### Scenario: Coste por ejercicio guardado
- **WHEN** se conoce el coste de la fase de generacion de un tech lead y los ejercicios guardados
- **THEN** el coste por ejercicio guardado es su cociente

#### Scenario: Coste por evaluacion
- **WHEN** se calcula el coste de evaluar una respuesta
- **THEN** es el del evaluador mas el del revisor

#### Scenario: Coste de formar a un alumno
- **WHEN** un equipo tiene dos alumnos que resuelven 500 ejercicios cada uno
- **THEN** el coste por alumno es 500 evaluaciones mas la mitad del coste de generacion del equipo

#### Scenario: Sin ahorros
- **WHEN** se presentan los costes unitarios
- **THEN** el informe no incluye ningun ahorro, retorno ni punto de equilibrio

### Requirement: Efecto de la memoria de los agentes
El sistema SHALL calcular el coste de generar con y sin acierto de memoria de los agentes web y de codigo, y SHALL estimar los fallos de memoria de una campana como el menor entre el numero de generaciones y el de claves distintas posibles segun los repositorios y tecnologias de un proyecto.

#### Scenario: Con acierto
- **WHEN** se calcula una generacion con acierto de memoria en web y codigo
- **THEN** no incluye el coste de esos dos agentes

#### Scenario: Claves distintas acotan los fallos
- **WHEN** un proyecto tiene 5 repositorios y 15 tecnologias y genera 112 veces
- **THEN** los fallos de memoria del agente de codigo son como mucho 75 y los del agente web como mucho 15

#### Scenario: Menos generaciones que claves
- **WHEN** las generaciones son menos que las claves posibles
- **THEN** los fallos no superan el numero de generaciones

#### Scenario: Sensibilidad
- **WHEN** se piden mas claves distintas por generacion que las del supuesto base
- **THEN** el informe muestra como cambia el coste de generar

### Requirement: Coste del modelo de respaldo
El sistema SHALL mantener en la tabla de precios el modelo de respaldo de cada rol con su precio por proveedor de inferencia, refrescable desde una fuente publica sin credenciales, y SHALL calcular el coste de las operaciones y de la campana con el respaldo y su sensibilidad a la fraccion de llamadas que caen en el, con los mismos tokens medidos.

#### Scenario: Rango de precios
- **WHEN** un modelo de respaldo tiene varios proveedores con precio
- **THEN** se calcula con el proveedor mas barato y con el mas caro, y el informe muestra el rango

#### Scenario: Mismos tokens
- **WHEN** se calcula el coste con el respaldo
- **THEN** se usan los tokens medidos con el modelo primario y solo cambian los precios

#### Scenario: Fraccion de llamadas
- **WHEN** se configuran las fracciones 0 %, 5 %, 20 % y 100 %
- **THEN** el coste con 0 % es el medido, el de 100 % es el del respaldo y los intermedios ponderan ambos

#### Scenario: Fraccion desconocida
- **WHEN** se presentan los resultados del respaldo
- **THEN** se declara que la fraccion real de llamadas que cae al respaldo no se mide y que son escenarios

#### Scenario: Respaldo sin precio
- **WHEN** falta el precio de un modelo de respaldo necesario para el calculo
- **THEN** el calculo falla indicando el modelo, en lugar de suponer un precio

### Requirement: Comparativa con modelos de referencia
El sistema SHALL calcular el coste de las mismas operaciones, con los mismos tokens medidos, usando los precios de un modelo de referencia por rol configurable en la tabla de precios, y SHALL informar la diferencia frente al coste medido.

#### Scenario: Mismos tokens
- **WHEN** se calcula el coste con el modelo de referencia
- **THEN** se usan los tokens medidos de cada llamada y solo cambian los precios

#### Scenario: Referencia por rol
- **WHEN** los roles web, codigo y ejercicios se asignan a un modelo y evaluador, revisor y validador a otro
- **THEN** cada agente se precia con el modelo de su rol

#### Scenario: Diferencia
- **WHEN** se muestra la comparativa
- **THEN** aparece el coste con ambos modelos y el factor entre ellos

### Requirement: Informe de costes reproducible
El sistema SHALL generar el informe de costes de forma determinista a partir de un informe de evaluacion real, la tabla de precios y el fichero de supuestos, en formato estructurado y en tablas legibles, indicando el numero de casos que respalda cada cifra.

#### Scenario: Reproducibilidad
- **WHEN** se calcula dos veces con las mismas entradas
- **THEN** los dos informes de costes son identicos

#### Scenario: Respaldo de cada cifra
- **WHEN** se muestra el coste medio de un agente
- **THEN** se indica de cuantos casos y llamadas sale

#### Scenario: Informe simulado
- **WHEN** se intenta calcular costes desde un informe de modo simulado
- **THEN** el calculo se rechaza indicando que requiere un informe real

### Requirement: Control del esfuerzo de razonamiento en modo real
El sistema SHALL permitir fijar, **solo en modo real**, el esfuerzo de razonamiento
de los modelos —un nivel de esfuerzo, un tope de tokens de razonamiento, o
desactivado— inyectando el parametro correspondiente en la llamada al modelo sin
modificar el codigo de los agentes y sin pisar lo que el agente ya envia en esa
llamada, y SHALL registrar en el informe el ajuste usado para poder comparar coste y
calidad entre ajustes.

#### Scenario: Ajuste por nivel de esfuerzo
- **WHEN** se ejecuta la evaluacion en modo real indicando un nivel de esfuerzo de razonamiento
- **THEN** cada llamada al modelo lleva ese nivel en el parametro de razonamiento, junto a los datos que el agente ya pone en la llamada, y el informe registra el ajuste

#### Scenario: Ajuste por tope de tokens
- **WHEN** se ejecuta en modo real indicando un tope de tokens de razonamiento
- **THEN** cada llamada al modelo lleva ese tope en el parametro de razonamiento y el informe registra el ajuste

#### Scenario: Razonamiento desactivado
- **WHEN** se ejecuta en modo real indicando el razonamiento desactivado
- **THEN** cada llamada al modelo pide que el razonamiento este desactivado y el informe registra el ajuste

#### Scenario: Ajuste invalido
- **WHEN** se indica un ajuste de razonamiento que no es un nivel conocido, un tope de tokens positivo ni la desactivacion
- **THEN** la ejecucion termina con error antes de llamar a ningun modelo

#### Scenario: Ajuste rechazado en modo simulado
- **WHEN** se indica un ajuste de razonamiento sin estar en modo real
- **THEN** la ejecucion lo rechaza, porque el doble guionizado no llama a ningun proveedor y el ajuste no tendria efecto

#### Scenario: Baseline sin ajuste
- **WHEN** se ejecuta en modo real sin indicar ningun ajuste de razonamiento
- **THEN** no se inyecta ningun parametro de razonamiento y el informe registra que no se fijo ninguno

### Requirement: Umbrales de calidad y gate
El sistema SHALL mantener en el repositorio una tabla de umbrales de las metricas de la suite, editable y ajustable por quien opera el sistema, y SHALL poder ejecutar el modo real en un modo bloqueante que termine con codigo distinto de cero si alguna metrica con casos incumple su umbral, nombrandola; y SHALL no evaluar las metricas sin casos, informandolas aparte.

#### Scenario: Umbral incumplido
- **WHEN** una metrica con casos queda por debajo de su umbral (o por encima, si el umbral es un maximo) en modo bloqueante
- **THEN** la ejecucion termina con codigo distinto de cero y nombra la metrica, su valor y su umbral

#### Scenario: Todo dentro de umbral
- **WHEN** todas las metricas con casos cumplen su umbral
- **THEN** la ejecucion termina con codigo cero

#### Scenario: Metrica sin casos
- **WHEN** una metrica no tiene casos
- **THEN** no se evalua contra su umbral y se informa como no evaluada, no como incumplida

#### Scenario: Modo bloqueante solo en real
- **WHEN** se pide el modo bloqueante fuera del modo real
- **THEN** la ejecucion lo rechaza antes de evaluar ningun caso

#### Scenario: Umbrales como dato
- **WHEN** se cambia un umbral en la tabla
- **THEN** el gate lo refleja sin tocar el codigo del arnes

#### Scenario: El modo real sin gate no bloquea
- **WHEN** se ejecuta el modo real sin el modo bloqueante
- **THEN** la ejecucion informa las metricas y termina con codigo cero
