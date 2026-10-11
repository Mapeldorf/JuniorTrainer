FROM python:3.12-slim

# git: lo necesita `app/memory.py` (_repo_identity) para `git rev-parse
# HEAD` / `git remote get-url origin` al calcular la clave de memoria
# larga (tarea 4.4). Sin esto, _repo_identity cae silenciosamente al
# fallback (hashear el propio repo_path) en TODOS los casos, no solo en
# el no-git documentado -- bug encontrado preparando el grupo 7 (ver
# design.md).
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8011

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8011"]
