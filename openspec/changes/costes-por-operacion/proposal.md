# Proposal

## Why

La sección 3.8 del capstone («Costes anticipados por nivel de uso») sigue pendiente y es una de las que pide la rúbrica. Hoy no hay ninguna cifra: no se sabe cuánto cuesta una generación, una evaluación o una validación, ni qué pasaría con el tope de 5 USD por clave de LiteLLM si el uso creciera. La suite de evaluación (`evals/`) ya ejecuta los seis agentes contra los modelos reales, así que medir es ahora barato.

Se ha comprobado que no hace falta construir una contabilidad nueva: cada respuesta de los agentes trae sus tokens (`usage_metadata`), con los de razonamiento aparte, y OpenRouter devuelve además el coste facturado de la llamada en `response_metadata.token_usage.cost`. Langfuse, en cambio, no devuelve ni tokens ni coste por su API (ya anotado en §3.8).

## What Changes

- El arnés de evaluación **captura tokens y coste por llamada** (entrada, salida, razonamiento, coste facturado si el proveedor lo informa) y los agrega en el informe por agente y por caso.
- Una **tabla de precios versionada** (`evals/prices.json`, con fecha y fuente) y un script que la refresca desde la API pública de modelos de OpenRouter.
- Un **calculador de costes** (`evals/costs.py`) que, a partir de un informe real, los precios y unos supuestos de uso editables, produce:
  - coste por operación (validar una tecnología, evaluar una respuesta, generar sin repositorio, generar con repositorio), desglosado por etapa;
  - coste de una **campaña de incorporación** en tres niveles de tamaño (1, 5 y 30 equipos, que son los 1, 5 y 30 tech leads de los niveles piloto, equipo y organización del capstone): el uso real no es estacionario, así que se modela por fases —generación inicial, resolución por los juniors en 2 semanas y régimen posterior con las incorporaciones anuales y la generación a demanda— y se compara el mes más cargado con el presupuesto de 5 USD/30 días por clave;
  - **costes unitarios de la formación**: coste por ejercicio guardado, por evaluación y por junior formado (sus evaluaciones más su parte de la generación del equipo), que son los números con los que se puede razonar la inversión;
  - efecto de la memoria de los agentes web y de código (con y sin acierto);
  - comparativa con un modelo de referencia: Opus 5.5 para web, código y ejercicios, y Haiku 5.5 para validador, evaluador y revisor;
- La sección §3.8 del capstone, redactada con los resultados.

### Supuestos (el usuario no los tiene claros; quedan como parámetros a validar)

- **Forma del uso (indicada por el usuario).** La unidad es el **equipo**: un tech lead y 2 juniors. El tech lead genera del orden de 500 ejercicios durante el primer mes y guarda el 90 % de los candidatos; los juniors del equipo deben resolver esos 500 en 2 semanas (**cada** junior resuelve los 500, confirmado por el usuario). Cada año se incorporan otros 2 juniors por equipo, que resolverán el catálogo ya existente. Después, el uso del tech lead es puntual y esporádico: añade ejercicios nuevos y elimina los existentes según el feedback de los juniors (eliminar no gasta modelo; los ejercicios nuevos sí cuestan su generación y las evaluaciones de su resolución). Un modelo mensual de régimen estacionario no representa esa ráfaga.
- **Qué domina el coste no se da por supuesto.** Se espera que pese más la evaluación y la revisión (muchas llamadas pequeñas) que la generación, pero una generación con repositorio es bastante más cara que una evaluación; el informe mostrará el reparto.
- **Supuestos de uso** (ejercicios guardados a generar por tech lead, ejercicios por generación, tasa de guardado, juniors por equipo, equipos por nivel, ejercicios resueltos por junior en la campaña, incorporaciones anuales, porcentaje con repositorio, repositorios y tecnologías por proyecto, ejercicios nuevos a demanda al año): se proponen valores por defecto, marcados como hipótesis, en un fichero editable. Los números del capstone se derivan de ese fichero, no están escritos en el texto. Cada generación pide **5 candidatos** (el máximo) y **cada junior resuelve los 500 ejercicios** (ambos confirmados por el usuario): son unas 112 generaciones por tech lead y 1.000 evaluaciones por equipo.
- **Tavily y GitHub entran en el cálculo.** GitHub no tiene coste (confirmado por el usuario); las lecturas se cuentan igualmente. Tavily hoy usa el plan gratuito (Researcher, 1.000 créditos al mes) y pasaría al plan **Project: 30 al mes con 4.000 créditos incluidos**, y 0,008 por crédito adicional (consultado en la página de precios y la documentación de Tavily, octubre de 2026). Una búsqueda básica consume 1 crédito y una avanzada 2; el agente no indica la profundidad, así que se parte de 1 crédito por búsqueda, un valor configurable que conviene contrastar con el panel de Tavily. El plan es una **cuota mensual de la organización**, no un coste por búsqueda: el cálculo suma la cuota de los meses con uso y los créditos que excedan los incluidos. Tavily publica el importe en dólares; el informe expresa todos los costes en USD y no convierte divisas.
- **Límites de un proyecto (indicados por el usuario).** Como máximo 5 repositorios y entre 10 y 15 tecnologías a evaluar. Acotan los fallos de memoria de un equipo: la clave de la memoria web es el conjunto de tecnologías y la del agente de código es repositorio + commit + tecnologías, de modo que hay un número máximo de claves distintas. En vez de una tasa de acierto arbitraria, los fallos se estiman como el menor de las generaciones y las claves posibles.
- **Los costes medidos son los de lo que respondió**: el modelo primario o, si falló, el de respaldo. El alias que ve el cliente no distingue cuál fue.
- **Los precios son los de OpenRouter en la fecha de consulta**; el respaldo en Hugging Face no se precia (no hay API pública equivalente).

### Fuera de alcance

**Cuantificar el ahorro o el retorno.** El capstone proponía el coste del no-sistema (horas de tech lead) como la cifra que justifica el proyecto. El usuario descarta cualquier cálculo de ahorro: ni horas del tech lead (su uso es puntual y condensado en una franja corta), ni inferencia o especificaciones que los juniors se ahorrarían después en tareas reales en proyectos, porque no es calculable, igual que no lo es el retorno de formar a un empleado. §3.8 da el **coste** de la formación y presenta su beneficio como una premisa cualitativa: preparar a los juniors para depurar cambios puntuales y atómicos sin recurrir a inferencia y para plantear mejores especificaciones. No se compara ni se calcula un punto de equilibrio.

Facturación real, alertas de gasto, optimización de prompts para gastar menos, el caché de prompts del proveedor (`input_cache_read`) y cualquier cambio en el código de los agentes.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `agent-evaluation`: añade la captura de tokens y coste, la tabla de precios y el cálculo de costes por operación, nivel de uso, caché y modelo de referencia.

## Impact

- `evals/` (captura en el envoltorio del modelo, informe, `prices.json`, `costs.py`, tests y README); sin cambios en `agents/`, backend, frontend ni CI salvo ejecutar los nuevos tests.
- `capstone/juniortrainer-capstone.md` §3.8 (y referencias cruzadas en §3.4, §5.7 y el glosario).
- Una consulta de lectura a la API pública de modelos de OpenRouter al refrescar precios.
- La ejecución real que alimenta las cifras consume presupuesto de las claves de LiteLLM.
