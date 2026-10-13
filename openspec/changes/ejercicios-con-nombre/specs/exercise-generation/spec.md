# Spec Delta

## ADDED Requirements

### Requirement: Nombre de cada ejercicio candidato
El sistema SHALL producir, para cada ejercicio candidato, un nombre corto (distinto del enunciado) de 8 palabras como maximo, contando como palabra cada secuencia de caracteres separada por espacios en blanco, que lo identifique de un vistazo sin repetir el enunciado completo.

#### Scenario: Candidatos de una generacion lista
- **WHEN** una generacion llega a Ready con sus candidatos
- **THEN** cada candidato trae un nombre de 8 palabras o menos, distinto de su enunciado

#### Scenario: Un nombre se pasa del limite
- **WHEN** al redactar los candidatos algun nombre sale con mas de 8 palabras
- **THEN** se vuelven a pedir los candidatos indicando que acorten los nombres que se pasaban, una sola vez

#### Scenario: El nombre sigue pasandose tras el segundo intento
- **WHEN** tras ese segundo intento algun nombre sigue teniendo mas de 8 palabras
- **THEN** la tarea del agente de ejercicios se da por fallida y la generacion queda en estado de error, sin devolver candidatos que incumplan el limite
