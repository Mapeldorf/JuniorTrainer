# Spec Delta

## Purpose

Define cómo el sistema pide al usuario una confirmación explícita (confirmar o cancelar) antes de continuar con una acción, de forma asíncrona y con una apariencia propia de la aplicación en vez de un diálogo nativo del sistema operativo.

## ADDED Requirements

### Requirement: Confirmación asíncrona antes de una acción
El sistema SHALL presentar un diálogo de confirmación con un título, un mensaje y dos acciones (confirmar y cancelar) antes de ejecutar una acción que lo requiera, y SHALL esperar la decisión del usuario antes de continuar; la acción protegida SHALL ejecutarse únicamente si el usuario confirma.

#### Scenario: El usuario confirma
- **WHEN** se abre un diálogo de confirmación y el usuario pulsa la acción de confirmar
- **THEN** la acción protegida se ejecuta

#### Scenario: El usuario cancela
- **WHEN** se abre un diálogo de confirmación y el usuario pulsa la acción de cancelar
- **THEN** la acción protegida no se ejecuta y el diálogo se cierra

### Requirement: Sin diálogos nativos del navegador
El sistema SHALL NOT usar un diálogo nativo del navegador o del sistema operativo (`window.confirm`, `window.alert`) para pedir una confirmación; toda confirmación SHALL presentarse con la apariencia visual propia de la aplicación.

#### Scenario: Cualquier confirmación de la aplicación
- **WHEN** la aplicación necesita que el usuario confirme o cancele una acción
- **THEN** se presenta con un diálogo propio de la aplicación, nunca con un `window.confirm()` nativo

### Requirement: Cierre con teclado
El sistema SHALL cerrar el diálogo de confirmación como una cancelación cuando el usuario pulsa la tecla Escape, y SHALL situar el foco inicial del diálogo en la acción de cancelar.

#### Scenario: Escape cancela
- **WHEN** un diálogo de confirmación está abierto y el usuario pulsa Escape
- **THEN** el diálogo se cierra y la acción protegida no se ejecuta, igual que si se hubiera pulsado cancelar

#### Scenario: Foco inicial
- **WHEN** se abre un diálogo de confirmación
- **THEN** el foco del teclado recae sobre la acción de cancelar, de modo que pulsar Enter sin mover el foco no confirma una acción destructiva por accidente

### Requirement: Textos configurables por cada uso
El sistema SHALL permitir que cada punto de la aplicación que pide una confirmación indique su propio título, mensaje, y el texto de las dos acciones, sin un texto fijo común a todos los casos.

#### Scenario: Confirmaciones con textos distintos
- **WHEN** dos puntos distintos de la aplicación piden una confirmación
- **THEN** cada uno puede mostrar su propio título, mensaje y texto de los botones, independientemente del otro
