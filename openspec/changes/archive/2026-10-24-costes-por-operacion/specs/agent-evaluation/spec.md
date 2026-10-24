# Spec Delta

## ADDED Requirements

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
