# Tasks

## 1. Filtrado de rutas

- [x] 1.1 En `agents/code/app/service.py`, dentro de `analyze_repo`, construir `valid_paths = {e.path for e in entries}` justo despues de obtener `entries`, y filtrar `chosen_paths` contra ese conjunto antes del bucle de lectura (las rutas que no esten se loguean con `logger.warning` igual que hoy se loguea un `GitHubRepoError`/`FileNotFoundError`, y se descartan sin llamar a `read_file`).
- [x] 1.2 Verificar que el modulo importa sin errores (`python -c "import app.service"` con el entorno del agente).

## 2. Verificacion manual

- [x] 2.1 Verificar manualmente (sin infraestructura de tests, igual que el resto de propuestas de seguridad del backend) que una `path` fuera del listado real se descarta sin llamar a la API de GitHub: con un script temporal o una sesion interactiva, invocar `analyze_repo` con `entries`/`chosen_paths` simulados donde `chosen_paths` incluya una ruta inventada (p. ej. `"../../.env"`) y una real, y comprobar que solo se intenta leer la ruta real (mock o spy sobre `read_file` que confirme que nunca se le llama con la ruta inventada). Verificado: `read_file` se llamo solo con `['src/App.jsx']`, con el warning `el modelo eligio una ruta fuera del repositorio: '../../.env'` en el log.
- [x] 2.2 Confirmar que el caso normal (todas las rutas elegidas existen en el listado) sigue leyendo y analizando los ficheros igual que antes del cambio, sin diferencias de comportamiento. Verificado en el mismo script: la ruta real se leyo y `analyze_repo` devolvio un `CodeAnalysisResult` normal.
