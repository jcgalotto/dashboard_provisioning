# Dashboard Provisioning

Proyecto migrado a arquitectura de dos capas con **FastAPI** y **React**.

## Requisitos
- Docker y docker-compose

## Configuración de entorno

1. Generar `.env` desde el ejemplo (opcional):
   ```bash
   cp .env.example .env
   ```
   o ejecutar el asistente interactivo:

   **Windows**
   ```bash
   py scripts/configure_env.py
   ```

   **Linux/Mac**
   ```bash
   python3 scripts/configure_env.py
   ```

2. Levantar contenedores:
   ```bash
   docker compose up --build
   ```

3. Verificar servicios:
   - Front: [http://localhost](http://localhost)
   - Health: [http://localhost/api/healthz](http://localhost/api/healthz)
   - Docs API: [http://localhost/api/docs](http://localhost/api/docs)

## Estructura
- `api/` – Backend FastAPI con conexión Oracle y WebSockets.
- `web/` – Frontend React + TypeScript (Vite).
- `ops/` – Configuración de Nginx.

## Desarrollo
- Backend:
  ```bash
  cd api
  uvicorn app.main:app --reload
  ```
- Frontend:
  ```bash
  cd web
  npm install
  npm run dev
  ```

### Variables de entorno
Ver `.env.example` para configurar conexión Oracle, JWT y rutas.

### Rutas API
- `GET /healthz`
- `GET /provisioning/interfaces?page=1&page_size=50`

Ejemplo:

```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/provisioning/interfaces?page=1&page_size=10"
```

## Tests
- Python: `pytest -q`
- Frontend: `npm test`

## Nota
Las consultas a Oracle requieren Instant Client o el modo *thin* de `oracledb`.
