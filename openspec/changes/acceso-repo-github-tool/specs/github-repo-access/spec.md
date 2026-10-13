# Spec Delta

## Purpose

Define cómo el sistema localiza, autentica y lee el contenido de un repositorio de GitHub (público o corporativo privado) para alimentar la generación de ejercicios, sin descargarlo ni almacenarlo en ninguna máquina de la aplicación.

## ADDED Requirements

### Requirement: Referencia de entrada del repositorio
El sistema SHALL aceptar el repositorio de una generación únicamente como una referencia `owner/repo` (texto), SHALL rechazar cualquier otra forma de entrada (URL completa, ruta de filesystem, fichero ZIP), y SHALL validar `owner` y `repo` por separado contra una expresión que solo permite caracteres alfanuméricos y guiones, sin `/`, `..` ni espacios.

#### Scenario: Referencia válida
- **WHEN** se inicia una generación con `owner` y `repo` compuestos solo de caracteres alfanuméricos y guiones
- **THEN** la generación acepta la referencia y continúa

#### Scenario: Se recibe una URL completa
- **WHEN** se intenta iniciar una generación pasando una URL completa de GitHub en lugar de `owner`/`repo`
- **THEN** la petición se rechaza y no se crea ninguna generación

#### Scenario: Se recibe un ZIP
- **WHEN** se intenta aportar el repositorio como un fichero ZIP
- **THEN** la petición se rechaza y no se crea ninguna generación

#### Scenario: Caracteres no permitidos en owner o repo
- **WHEN** `owner` o `repo` contienen un carácter fuera de alfanuméricos y guiones (por ejemplo `/`, `..` o un espacio)
- **THEN** la petición se rechaza y no se crea ninguna generación

### Requirement: El repositorio nunca se descarga ni se almacena
El sistema SHALL leer el contenido del repositorio exclusivamente mediante llamadas bajo demanda a la API de GitHub, y SHALL NOT escribir el repositorio, en todo o en parte, en disco local ni en ningún volumen de la aplicación.

#### Scenario: Generación con repositorio
- **WHEN** una generación incluye un repositorio
- **THEN** el contenido leído llega únicamente a través de llamadas a la API de GitHub, sin que exista en ningún momento una copia del repositorio en disco

### Requirement: Autenticación mediante GitHub App de solo lectura
El sistema SHALL autenticar toda llamada a la API de GitHub con credenciales de una GitHub App instalada únicamente en los repositorios corporativos autorizados, con permiso de solo lectura sobre el contenido, y SHALL mantener la clave privada de esa App fuera de código fuente y de variables de entorno en texto plano.

#### Scenario: Acceso a un repositorio con la App instalada
- **WHEN** se solicita el contenido de un repositorio en el que la GitHub App está instalada
- **THEN** la llamada se autentica con un token de instalación de esa App y tiene éxito

#### Scenario: Acceso a un repositorio sin la App instalada
- **WHEN** se solicita el contenido de un repositorio en el que la GitHub App no está instalada
- **THEN** la llamada a la API de GitHub falla por falta de autorización, y esa generación trata el fallo como fallo del agente de código

### Requirement: Host de la API fijo, sin URLs de usuario
El sistema SHALL construir toda llamada a la API de GitHub contra un host fijo de configuración, SHALL NOT aceptar ni interpolar una URL o host proporcionado por el usuario en esa llamada, y SHALL NOT seguir redirecciones HTTP hacia un host distinto del configurado.

#### Scenario: Construcción de la llamada
- **WHEN** el sistema necesita leer el árbol o el contenido de un fichero de un repositorio
- **THEN** la URL de la llamada se construye únicamente a partir del host fijo de configuración, `owner` y `repo`, sin ningún fragmento de URL proporcionado por el usuario

#### Scenario: Redirección a otro host
- **WHEN** la API de GitHub responde con una redirección hacia un host distinto del configurado
- **THEN** el sistema no sigue esa redirección y trata la llamada como fallida

### Requirement: Commit fijado por generación
El sistema SHALL resolver el commit `HEAD` del repositorio una sola vez al iniciar una generación, y SHALL usar ese mismo `commit_sha` en todas las llamadas de lectura de esa generación.

#### Scenario: Varias lecturas dentro de la misma generación
- **WHEN** una generación con repositorio hace más de una llamada de lectura a la API de GitHub
- **THEN** todas esas llamadas usan el mismo `commit_sha`, resuelto una sola vez al iniciar la generación

### Requirement: Contenido del repositorio tratado como datos, no como instrucciones
El sistema SHALL insertar el contenido leído del repositorio en el prompt del modelo siempre delimitado explícitamente como datos, y SHALL instruir al modelo para ignorar cualquier texto dentro de ese contenido que parezca dirigido a él.

#### Scenario: El código leído contiene texto dirigido al modelo
- **WHEN** un fichero leído del repositorio contiene un comentario o cadena que parece una instrucción dirigida al modelo
- **THEN** el modelo no cambia su comportamiento de análisis por ese texto, y el resultado de la tarea no refleja haber seguido esa instrucción

### Requirement: Registro de auditoría de cada acceso
El sistema SHALL registrar, para cada generación que incluya repositorio, un registro de auditoría con la generación, el tech lead que la inició, `owner`, `repo`, el `commit_sha` resuelto, el momento, y si el acceso tuvo éxito o falló, antes de pasar ningún contenido al agente de código.

#### Scenario: Generación con repositorio
- **WHEN** una generación con repositorio invoca la tool de acceso a GitHub
- **THEN** queda un registro de auditoría con la generación, el tech lead, `owner/repo`, el `commit_sha` y el resultado del acceso

### Requirement: Listado del árbol en una sola llamada
El sistema SHALL obtener el listado completo de ficheros de un repositorio mediante una única llamada recursiva a la API de árbol de Git, en vez de recorrer directorios uno a uno, para minimizar el número de peticiones contra el límite de tasa de la API de GitHub.

#### Scenario: Listar un repositorio
- **WHEN** el agente de código necesita el listado de ficheros de un repositorio
- **THEN** ese listado se obtiene con una sola llamada a la API, sin una llamada adicional por cada directorio
