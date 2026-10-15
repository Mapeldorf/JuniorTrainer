# frontend-ui-theme Specification

## Purpose
Define el lenguaje visual con el que se presenta toda la aplicación: un tema oscuro único, tipografía del sistema tipo Apple, un layout estrecho y centrado, y un conjunto compartido de superficies, botones, campos y estados de interacción que se ven igual en todas las pantallas.

## Requirements

### Requirement: Tema oscuro único
El sistema SHALL presentar toda la interfaz sobre un tema oscuro —superficies oscuras y texto claro— de forma uniforme en todas las pantallas, y SHALL NOT ofrecer un tema claro alternativo ni cambiar de tema según la preferencia del sistema.

#### Scenario: Cualquier pantalla de la aplicación
- **WHEN** el usuario abre cualquier pantalla (auth, home, alumno o tech-lead)
- **THEN** la pantalla se muestra sobre superficies oscuras con texto claro y contraste legible

#### Scenario: Sin tema claro
- **WHEN** la aplicación se carga
- **THEN** no existe ningún control ni detección automática que cambie a un tema claro

### Requirement: Tipografía del sistema tipo Apple
El sistema SHALL usar exclusivamente un stack de fuentes del sistema operativo que priorice SF Pro en plataformas Apple y use alternativas nativas en el resto, y SHALL NOT cargar fuentes web externas ni realizar peticiones de fuentes a terceros.

#### Scenario: Dispositivo Apple
- **WHEN** la aplicación se renderiza en una plataforma Apple
- **THEN** el texto usa la fuente del sistema SF Pro

#### Scenario: Sin fuentes externas
- **WHEN** la aplicación se carga
- **THEN** no se realiza ninguna petición a `fonts.googleapis.com` ni a `fonts.gstatic.com`

### Requirement: Layout estrecho y centrado
El sistema SHALL presentar el contenido dentro de un contenedor de ancho máximo, centrado y con padding lateral reducido, de forma que la línea de lectura no ocupe todo el ancho de la ventana en pantallas grandes.

#### Scenario: Ventana ancha
- **WHEN** el viewport es más ancho que el ancho máximo de contenido
- **THEN** el contenido se limita a ese ancho máximo y queda centrado, con márgenes laterales visibles

#### Scenario: Ventana estrecha
- **WHEN** el viewport es más estrecho que el ancho máximo de contenido
- **THEN** el contenido se adapta sin provocar desplazamiento horizontal de la página

### Requirement: Lenguaje visual consistente entre pantallas
El sistema SHALL construir superficies, botones, campos de formulario y etiquetas de estado a partir de un conjunto compartido de estilos, de modo que elementos equivalentes tengan la misma apariencia en todas las pantallas.

#### Scenario: Elementos equivalentes
- **WHEN** dos pantallas distintas muestran el mismo tipo de elemento (por ejemplo, un botón primario o una tarjeta de contenido)
- **THEN** ambos se ven con la misma superficie, forma y color

#### Scenario: Estados de resultado en el ejercicio
- **WHEN** un ejercicio ya respondido muestra su veredicto (correcto, incompleto o incorrecto)
- **THEN** cada veredicto usa un color de estado distinguible y legible sobre el fondo oscuro

### Requirement: Estados de interacción accesibles sobre fondo oscuro
El sistema SHALL mostrar un indicador de foco visible, estados hover y estados deshabilitados distinguibles, y contraste suficiente, para todos los elementos interactivos sobre las superficies oscuras.

#### Scenario: Navegación con teclado
- **WHEN** el usuario mueve el foco con el teclado sobre un elemento interactivo
- **THEN** el elemento muestra un indicador de foco visible sobre el fondo oscuro

#### Scenario: Elemento deshabilitado
- **WHEN** un botón o campo está deshabilitado
- **THEN** se distingue visualmente de su estado habilitado y no parece interactivo

### Requirement: El bloque de código y el diálogo de confirmación siguen el tema
El sistema SHALL mostrar el bloque de código de los ejercicios y el diálogo de confirmación con la misma identidad visual del tema oscuro, manteniendo el código legible y el diálogo claramente separado del contenido de detrás.

#### Scenario: Bloque de código
- **WHEN** un ejercicio muestra código fuente
- **THEN** el bloque de código es legible sobre una superficie coherente con el tema oscuro

#### Scenario: Diálogo de confirmación
- **WHEN** se abre una confirmación sobre una pantalla oscura
- **THEN** el diálogo se distingue del contenido de detrás y sus botones respetan los estados de interacción del tema
