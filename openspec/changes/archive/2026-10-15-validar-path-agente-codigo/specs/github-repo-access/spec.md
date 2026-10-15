# Spec Delta

## ADDED Requirements

### Requirement: Rutas de fichero restringidas al listado real del repositorio
El sistema SHALL leer, al analizar un repositorio, unicamente rutas de fichero que esten literalmente presentes en el listado obtenido para ese `commit_sha` mediante la API de arbol de Git, y SHALL descartar sin leer cualquier ruta elegida por el modelo que no figure en ese listado.

#### Scenario: El modelo elige una ruta fuera del repositorio
- **WHEN** el modelo que elige ficheros a analizar devuelve una ruta que no esta en el listado real del repositorio para el `commit_sha` resuelto (p. ej. `../../algo`, una ruta absoluta, o cualquier otra que no figure en el arbol)
- **THEN** el sistema no hace ninguna llamada a la API de GitHub con esa ruta, la descarta igual que un fichero no encontrado, y continua con el resto de rutas elegidas

#### Scenario: El modelo elige rutas que si existen en el repositorio
- **WHEN** todas las rutas elegidas por el modelo estan presentes en el listado real del repositorio
- **THEN** el sistema las lee con normalidad, sin cambio de comportamiento respecto a hoy
