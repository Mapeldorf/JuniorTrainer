# user-auth Specification

## Purpose

Define como entra cada usuario a JuniorTrainer: quien puede darse de alta, como recupera el acceso si lo pierde, y que identifica a cada peticion autenticada.

## Requirements

### Requirement: Sin autorregistro
El sistema SHALL mantener desactivado el alta publica. Toda cuenta nace de uno de dos origenes: el script de carga inicial (tech lead) o una invitacion de un tech lead (alumno).

#### Scenario: No existe un formulario de alta publica
- **WHEN** alguien sin invitacion intenta crear una cuenta directamente en Supabase Auth con email y contrasena
- **THEN** el alta es rechazada porque el registro publico esta desactivado en el proyecto

### Requirement: Alta del primer tech lead
El sistema SHALL ofrecer un script de carga inicial que cree una cuenta con `role = tech_lead` ya confirmada y con contrasena, sin pasar por invitacion por email.

#### Scenario: Ejecutar el script de carga inicial
- **WHEN** se ejecuta `seed_tech_lead.py` con un email, un nombre y una contrasena de al menos 8 caracteres
- **THEN** Supabase Auth crea el usuario con el email confirmado y esa contrasena, y el trigger de alta crea su `profile` con `role = tech_lead` y el nombre dado

### Requirement: Alta de alumnos por invitacion
El sistema SHALL permitir que un tech lead de de alta a un alumno indicando su nombre y su email; el alumno SHALL recibir un correo para elegir su propia contrasena, sin contrasena temporal.

#### Scenario: Tech lead invita a un alumno nuevo
- **WHEN** un tech lead autenticado llama a `POST /users` con un nombre y un email que no existe todavia
- **THEN** Supabase envia al alumno un correo de invitacion con un enlace para elegir contrasena, y al confirmarse el alta el trigger crea su `profile` con `role = student` y ese nombre

#### Scenario: El email ya tiene cuenta
- **WHEN** un tech lead llama a `POST /users` con un email que ya pertenece a un usuario existente
- **THEN** la peticion responde 409 y no se envia ninguna invitacion

#### Scenario: Un alumno no puede invitar
- **WHEN** un usuario autenticado con `role = student` llama a `POST /users`
- **THEN** la peticion responde 403 y no se envia ninguna invitacion

### Requirement: Recuperacion de contrasena
El sistema SHALL permitir recuperar el acceso mediante un enlace de un solo uso enviado por correo, sin revelar si un email tiene cuenta o no.

#### Scenario: Solicitar recuperacion con un email existente
- **WHEN** alguien pide recuperar la contrasena de un email que tiene cuenta
- **THEN** recibe un correo de Supabase con un enlace de un solo uso para elegir otra contrasena, y la respuesta del formulario es indistinguible de la de un email sin cuenta

#### Scenario: Solicitar recuperacion con un email que no existe
- **WHEN** alguien pide recuperar la contrasena de un email sin cuenta
- **THEN** el formulario responde igual que si el email existiera, y no se envia ningun correo

### Requirement: Sesion mediante JWT de Supabase
El sistema SHALL identificar cada peticion autenticada mediante un JWT emitido por Supabase Auth, resuelto a un `profile` (nombre y rol) antes de aplicar cualquier regla de autorizacion.

#### Scenario: Peticion sin token
- **WHEN** se llama a un endpoint que requiere autenticacion sin cabecera `Authorization`
- **THEN** la peticion responde 401

#### Scenario: Token invalido o caducado
- **WHEN** se llama a un endpoint que requiere autenticacion con un JWT invalido, manipulado o caducado
- **THEN** la peticion responde 401

### Requirement: Listar alumnos
El sistema SHALL permitir a un tech lead listar los alumnos existentes (identificador, nombre y email), y SHALL rechazar esta consulta si la hace un alumno.

#### Scenario: Tech lead lista los alumnos
- **WHEN** un tech lead autenticado llama a `GET /users`
- **THEN** recibe la lista de todos los alumnos existentes con su identificador, nombre y email

#### Scenario: Un alumno no puede listar alumnos
- **WHEN** un usuario autenticado con `role = student` llama a `GET /users`
- **THEN** la peticion responde 403 y no devuelve ningun dato
