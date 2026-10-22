# Spec Delta

## Purpose

Define la evaluación reproducible de los agentes sobre un dataset dorado versionado en el repositorio, con métricas deterministas, un modo simulado apto para integración continua y un modo real contra modelos, para poder detectar si un cambio de código, de prompt o de modelo empeora el sistema.

## ADDED Requirements

### Requirement: Dataset dorado versionado en el repositorio
El sistema SHALL mantener en el repositorio un dataset dorado con cuatro conjuntos (generacion, evaluacion, validacion y adversarial), en un formato de texto legible por diff, donde cada caso lleva un identificador unico y su resultado esperado o la propiedad verificable que debe cumplir.

#### Scenario: Cuatro conjuntos presentes
- **WHEN** se carga el dataset
- **THEN** existen los cuatro conjuntos y cada uno tiene al menos un caso

#### Scenario: Identificadores unicos
- **WHEN** se carga el dataset
- **THEN** no hay dos casos con el mismo identificador dentro de un conjunto

#### Scenario: Caso mal formado
- **WHEN** un caso carece de un campo obligatorio de su conjunto o trae un valor fuera de rango
- **THEN** la carga falla indicando el conjunto, el caso y el campo, sin ejecutar ningun agente

#### Scenario: Etiquetas de evaluacion cubren los tres veredictos
- **WHEN** se carga el conjunto de evaluacion
- **THEN** contiene casos etiquetados como `correct`, `incomplete` e `incorrect`, incluidos casos limite

### Requirement: Modo simulado sin red ni credenciales
El sistema SHALL poder ejecutar la evaluacion en modo simulado, sustituyendo el modelo de cada agente por un doble guionizado por el propio caso, sin acceso a red, a LiteLLM, a la base de datos ni a credenciales, de modo que el resultado dependa solo del codigo de los agentes y del dataset.

#### Scenario: Ejecucion sin entorno
- **WHEN** se ejecuta el modo simulado sin ninguna variable de entorno de credenciales ni servicio levantado
- **THEN** la ejecucion termina y produce el informe

#### Scenario: Resultado reproducible
- **WHEN** se ejecuta el modo simulado dos veces sobre el mismo codigo y dataset
- **THEN** las metricas no temporales de ambos informes son identicas

#### Scenario: El codigo real del agente se ejecuta
- **WHEN** el doble de un caso devuelve una respuesta que incumple el contrato (JSON invalido, veredicto fuera de rango, justificacion de mas de 50 palabras)
- **THEN** el agente reacciona con su logica real de validacion y reintento, y el informe refleja ese comportamiento

### Requirement: Modo real contra el stack
El sistema SHALL poder ejecutar la misma evaluacion en modo real, llamando a los agentes con sus modelos a traves de LiteLLM, de forma explicita y nunca por defecto, e indicando en el informe el modo y los alias de modelo usados.

#### Scenario: El modo real exige pedirse
- **WHEN** se ejecuta la evaluacion sin indicar el modo
- **THEN** se usa el modo simulado

#### Scenario: Stack no disponible
- **WHEN** se pide el modo real y LiteLLM no responde o falta la credencial del agente
- **THEN** la ejecucion falla antes de evaluar ningun caso, indicando que falta

#### Scenario: Sin escrituras
- **WHEN** se ejecuta cualquiera de los dos modos
- **THEN** no se escribe en la base de datos ni se persiste ningun ejercicio, respuesta o generacion

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
El sistema SHALL medir el porcentaje de casos en los que el agente necesito su unico reintento correctivo, contando las llamadas al modelo por caso, sin depender de logs ni de modificar el agente.

#### Scenario: Sin reintento
- **WHEN** un caso se resuelve con una sola llamada al modelo
- **THEN** no cuenta como reintento

#### Scenario: Con reintento
- **WHEN** un caso requiere una segunda llamada al modelo por una respuesta que incumplia el contrato
- **THEN** cuenta como activacion del reintento, aunque el resultado final sea correcto

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
El sistema SHALL incluir en el conjunto adversarial casos de texto no confiable (respuestas de alumno que intentan fijar el veredicto, tecnologias que son instrucciones o datos personales), y SHALL comprobar de forma determinista que el contenido no confiable viaja delimitado como dato en el prompt que recibe el modelo.

#### Scenario: Respuesta de alumno delimitada
- **WHEN** el evaluador recibe una respuesta de alumno del conjunto adversarial
- **THEN** el prompt enviado al modelo contiene esa respuesta entre los delimitadores de dato, y no fuera de ellos

#### Scenario: Dato personal en una tecnologia
- **WHEN** una entrada adversarial del validador contiene un dato personal reconocible por el pre-filtro
- **THEN** el validador la rechaza antes de llamar al modelo

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
