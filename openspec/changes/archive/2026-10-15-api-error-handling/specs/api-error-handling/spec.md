# Spec Delta

## Purpose

Garantiza que las respuestas de error HTTP del backend no exponen detalles internos (excepciones de librerias externas, texto de errores de agentes) a los clientes de la API.

## ADDED Requirements

### Requirement: Respuesta generica al fallar la invitacion de un alumno
El sistema SHALL devolver, cuando `POST /users` falla por un error de la Admin API de Supabase, un `HTTPException` 409 cuyo `detail` sea un mensaje generico que no incluya el texto de la excepcion original.

#### Scenario: Fallo al invitar por email ya existente u otro error de Supabase
- **WHEN** la Admin API de Supabase falla al invitar a un email
- **THEN** la respuesta es `409 Conflict` con un mensaje generico de conflicto, sin el texto de la excepcion de Supabase

### Requirement: Registro en servidor del fallo de invitacion
El sistema SHALL registrar en el log del servidor la excepcion completa capturada al fallar la invitacion de un alumno, para no perder la causa raiz al dejar de exponerla en la respuesta HTTP.

#### Scenario: Log del fallo
- **WHEN** la Admin API de Supabase falla al invitar a un email
- **THEN** el servidor registra en su log la excepcion original con suficiente detalle para diagnosticar la causa

### Requirement: Respuesta generica al fallar la evaluacion de una respuesta
El sistema SHALL devolver, cuando la evaluacion de una respuesta de un alumno falla (`AnswerEvaluationFailed`), un `HTTPException` 502 cuyo `detail` sea un mensaje generico que no incluya el texto de la excepcion original del agente evaluador/revisor.

#### Scenario: Fallo del agente evaluador o revisor
- **WHEN** el agente evaluador o el agente revisor fallan al evaluar una respuesta
- **THEN** la respuesta es `502 Bad Gateway` con un mensaje generico, sin el texto de la excepcion del agente

### Requirement: Registro en servidor del fallo de evaluacion
El sistema SHALL registrar en el log del servidor la excepcion completa capturada al fallar la evaluacion de una respuesta, ademas de seguir guardando el detalle en `answer_evaluation.error_message` como hace hoy.

#### Scenario: Log del fallo de evaluacion
- **WHEN** la evaluacion de una respuesta falla
- **THEN** el servidor registra en su log la excepcion original con suficiente detalle para diagnosticar la causa, sin dejar de guardar `answer_evaluation.error_message` como hoy
