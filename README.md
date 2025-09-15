# Dashboard Provisioning

Proyecto migrado a arquitectura de dos capas con **FastAPI** y **React**.

## Requisitos
- Docker y docker-compose

## Ejecución

1. Copiar `.env.example` a `.env` y ajustar variables.
2. Construir y ejecutar contenedores:
   ```bash
   docker compose up --build
   ```
3. Navegar a [http://localhost](http://localhost).

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
