
# ANVIORA — Fase 5: *Operate* (microservicios)

Sistema inteligente para el monitoreo, análisis y seguimiento del bienestar emocional.
Esta fase lleva el backend de las Fases 1–4 a **4 servicios independientes** y agrega todo lo necesario para **operarlos**: contenedores, chequeos de salud, logs, métricas, alertas y respaldos.

> ANVIORA es una herramienta de autoconocimiento y seguimiento preventivo. **No es un dispositivo médico ni reemplaza la atención psicológica o psiquiátrica profesional.**

**Autor:** Adrian Ferley Figueroa Flórez · Tecnología en Desarrollo de Sistemas Informáticos · UTS

---

## Arquitectura

```
Navegador ──► gateway (Nginx :8000) ──┬─► auth-service            :8001   login, registro, JWT
                │                      ├─► recommendation-service  :8003   reglas de autocuidado
                │ sirve el frontend    └─► core-api                :8004   registros diarios y dashboard
                                                   │
                                                   └──(HTTP interno)──► analysis-service :8002   anonimiza + sentimiento (IA)
                         Todos ──► PostgreSQL (base de datos compartida)
```

| Servicio | Qué hace | Base de datos |
|---|---|---|
| `gateway` | Único punto de entrada; reparte las rutas y sirve el frontend | — |
| `auth-service` | Registro, login y emisión de JWT | Sí |
| `core-api` | Registros diarios y dashboard; coordina el análisis | Sí |
| `analysis-service` | Anonimiza el texto y calcula el sentimiento (pysentimiento) | No |
| `recommendation-service` | Motor de reglas y consulta de recomendaciones | Sí |

Las rutas `/internal/*` (comunicación entre servicios) **no salen por el gateway** y exigen una clave compartida.

---

## Inicio rápido (Docker)

Requisitos: Docker Desktop y ~4 GB libres (la imagen de IA incluye PyTorch).

```powershell
Copy-Item .env.example .env      # luego edita .env con tus propios valores
docker compose up -d --build
docker compose ps                # todos deben quedar "healthy"
```

Abre **http://localhost:8000**. La primera vez, `analysis-service` descarga el modelo de IA y tarda unos minutos; el resto de la aplicación funciona mientras tanto.

| Quiero… | Comando |
|---|---|
| Ver los logs de un servicio | `docker compose logs -f core-api` |
| Ver cada servicio por separado (`/docs`, `/health`) | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` |
| Gráficas y alertas (Grafana en `:3000`, Prometheus en `:9090`) | `docker compose --profile monitoring up -d` |
| Apagar conservando los datos | `docker compose down` |

Toda la guía de operación (salud, logs, métricas, respaldos y qué hacer ante fallas) está en **[`docs/OPERACION.md`](docs/OPERACION.md)**.

---

## Ejecutar sin Docker (alternativa)

Necesitas Python 3.11+ y PostgreSQL instalado, con la base creada y el esquema cargado (`psql -f database/schema.sql`). Repite esto para cada carpeta de `services/` (en 4 terminales):

```powershell
cd services\core-api
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:DATABASE_URL         = "postgresql://usuario:clave@localhost:5432/anviora_db"
$env:JWT_SECRET_KEY       = "una-clave-larga-y-aleatoria"
$env:INTERNAL_API_KEY     = "otra-clave-larga-y-aleatoria"      # igual en los 4 servicios
$env:ANALYSIS_SERVICE_URL = "http://localhost:8002"
$env:RECOMMENDATION_SERVICE_URL = "http://localhost:8003"

uvicorn app.main:app --port 8004
```

Cada servicio usa su puerto de la tabla de arriba. `analysis-service` no necesita `DATABASE_URL`.

> Sin Docker puedes probar cada servicio por separado desde su Swagger (`http://localhost:8004/docs`, etc.), pero **la aplicación web completa necesita el gateway**: el frontend usa una sola dirección y es Nginx quien reparte las rutas entre los 4 servicios. Por eso Docker es la forma recomendada de usarla.

---

## Pruebas

Cada servicio tiene sus propias pruebas (no necesitan base de datos real):

```powershell
cd services\core-api
python -m pytest -q
```

Repite en `auth-service`, `analysis-service` y `recommendation-service`.

---

## Estructura

```
anviora/
├── docker-compose.yml          # base de datos, 4 servicios, gateway, respaldos y monitoreo
├── docker-compose.dev.yml      # extra de desarrollo: expone cada servicio
├── .env.example                # copia a .env y edita (el .env NO se sube a git)
├── gateway/                    # Nginx: rutas, límite de peticiones en login, bloqueo de /internal
├── services/
│   ├── auth-service/
│   ├── core-api/
│   ├── analysis-service/
│   └── recommendation-service/ # cada uno con app/, tests/, Dockerfile y requirements.txt
├── frontend/                   # HTML/CSS/JS (Fase 3)
├── database/schema.sql         # esquema de PostgreSQL (Fase 1)
├── ops/monitoring/             # Prometheus, alertas y panel de Grafana
└── docs/OPERACION.md           # guía de operación y runbook
```
# ANVIORA
Sistema inteligente para el monitoreo, análisis y seguimiento del bienestar emocional. Esta fase lleva el backend de las Fases 1–4 a **4 servicios independientes** y agrega todo lo necesario para **operarlos**: contenedores, chequeos de salud, logs, métricas, alertas y respaldos.

