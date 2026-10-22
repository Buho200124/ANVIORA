# ANVIORA — Fase *Operate*: guía de operación

**Autor:** Adrian Ferley Figueroa Flórez · **Institución:** Unidades Tecnológicas de Santander (UTS)

Este documento explica cómo se **opera** ANVIORA una vez desplegado: cómo se levanta, cómo se sabe que está sano, cómo se observa, cómo se respalda y qué hacer cuando algo falla.

---

## 1. Arquitectura de microservicios

```
                    Navegador
                        │
                        ▼  :8000  (único puerto expuesto)
              ┌───────────────────┐
              │  Gateway (Nginx)  │  sirve el frontend y reparte /api/*
              └───────┬───────────┘
      /api/auth       │ /api/logs · /api/analysis · /api/dashboard      /api/recommendations
         ┌────────────┼───────────────────────┐                              │
         ▼            ▼                       │                              ▼
 ┌──────────────┐ ┌──────────────┐           │                     ┌────────────────────┐
 │ auth-service │ │   core-api   │───────────┼──── HTTP interno ───▶│ recommendation-    │
 │    :8001     │ │    :8004     │           │  /internal/evaluate  │ service  :8003     │
 └──────┬───────┘ └──────┬───────┘           │                     └─────────┬──────────┘
        │                │  HTTP interno     ▼                               │
        │                └──────────▶ ┌──────────────────┐                    │
        │                /internal/   │ analysis-service │                    │
        │                analyze      │  :8002 (IA)      │                    │
        │                             └──────────────────┘                    │
        └─────────────────────────┬───────────────────────────────────────────┘
                                  ▼
                          ┌───────────────┐
                          │  PostgreSQL   │  (base de datos compartida)
                          └───────────────┘
```

| Servicio | Responsabilidad | Puerto interno | Usa BD |
|---|---|---|---|
| `gateway` | Punto de entrada, frontend, límite de peticiones en login, bloquea `/internal` | 80 → **8000** | No |
| `auth-service` | Registro, login y emisión de JWT (RF-01) | 8001 | Sí |
| `analysis-service` | Anonimización de PII y análisis de sentimiento con pysentimiento (RF-03) | 8002 | **No** |
| `recommendation-service` | Motor de reglas de autocuidado (RF-04) | 8003 | Sí |
| `core-api` | Registros diarios, consulta de análisis y dashboard (RF-02, RF-05) | 8004 | Sí |
| `db` | PostgreSQL 16 | 5432 | — |
| `backup` | Respaldo automático diario | — | Lee |

**Cómo se hablan entre sí.** Cuando el usuario guarda un registro, `core-api` lo almacena y responde de inmediato. En segundo plano llama a `analysis-service` (`POST /internal/analyze`), guarda el resultado y luego llama a `recommendation-service` (`POST /internal/evaluate`). Si uno de los dos falla, el sistema se degrada de forma segura: el registro del usuario nunca se pierde.

**Seguridad entre servicios.** Los endpoints `/internal/*` exigen la cabecera `X-Internal-Key` y además el gateway los bloquea desde afuera (responde 404).

---

## 2. Puesta en marcha

### Requisitos
- Docker Desktop (Windows/Mac) o Docker Engine + Compose (Linux)
- ~4 GB de espacio libre (la imagen de `analysis-service` incluye PyTorch)

### Pasos (PowerShell en Windows)

```powershell
# 1. Crear el archivo de configuración y editarlo con tus valores
Copy-Item .env.example .env
notepad .env

# 2. Construir y levantar todo
docker compose up -d --build

# 3. Ver que todo quede "healthy"
docker compose ps
```

> **Primera vez:** `analysis-service` descarga el modelo de pysentimiento (puede tardar varios minutos). Se guarda en el volumen `modelos_hf`, así que los siguientes arranques son rápidos. Mientras carga, su `/ready` responde 503; es normal.

Abre **http://localhost:8000** para usar la aplicación.

### Modo desarrollo/demostración (expone cada servicio)

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Con eso puedes abrir, por ejemplo, `http://localhost:8004/docs` (Swagger del core-api) o `http://localhost:8002/ready`.

### Apagar y reiniciar

```powershell
docker compose down            # apaga; los datos se conservan
docker compose restart core-api  # reinicia un solo servicio
docker compose down -v         # ⚠️ apaga Y BORRA todos los datos (volúmenes)
```

> El `schema.sql` se aplica **solo la primera vez**, cuando el volumen de la base de datos está vacío. Si cambias el esquema, tendrás que migrarlo a mano o recrear el volumen (perdiendo datos).

---

## 3. Salud de los servicios (health checks)

Cada microservicio expone tres endpoints:

| Endpoint | Pregunta que responde | Si falla |
|---|---|---|
| `/health` (*liveness*) | ¿El proceso está vivo? | Docker marca el contenedor `unhealthy` y `restart: unless-stopped` lo reinicia si se cae |
| `/ready` (*readiness*) | ¿Puede atender tráfico? (BD alcanzable, modelo cargado) | Responde **503** con el detalle de qué falló |
| `/metrics` | Métricas en formato Prometheus | — |

Ejemplo de `/ready` cuando el modelo aún carga:

```json
{ "estado": "no_listo", "servicio": "analysis-service",
  "comprobaciones": { "modelo_cargado": "fallo" } }
```

Revisión rápida del estado global:

```powershell
docker compose ps
Invoke-RestMethod http://localhost:8000/gateway/health
```

---

## 4. Observabilidad

### 4.1 Logs

Todos los servicios escriben **una línea JSON por evento** con fecha, nivel, servicio, mensaje y un `request_id`:

```json
{"ts": "2026-10-13T18:40:02+00:00", "nivel": "INFO", "servicio": "core-api", "logger": "anviora.http", "mensaje": "POST /api/logs -> 201 (48 ms)", "request_id": "9f3c1a7be204"}
```

El `request_id` lo genera el gateway y viaja por todos los servicios, así puedes **seguir una misma operación** a través de varios logs:

```powershell
docker compose logs -f core-api                         # un servicio, en vivo
docker compose logs --since 10m                         # todos, últimos 10 minutos
docker compose logs | Select-String "9f3c1a7be204"      # seguir una petición por su ID
docker compose logs | Select-String '"nivel": "ERROR"'   # solo errores
```

Los logs rotan automáticamente (3 archivos de 10 MB por servicio) para no llenar el disco. El nivel se cambia con `LOG_LEVEL` en `.env` (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

> **Privacidad:** el `analysis-service` nunca escribe en logs el texto que escribe el usuario, solo el resultado del análisis.

### 4.2 Métricas

Cada servicio publica:

- `anviora_http_requests_total{servicio, metodo, ruta, estado}` — peticiones totales
- `anviora_http_request_duration_seconds` — duración (histograma)

Para verlas con gráficas, levanta el perfil de monitoreo:

```powershell
docker compose --profile monitoring up -d
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (usuario `admin`, clave `GRAFANA_ADMIN_PASSWORD` de tu `.env`)

Ambos escuchan **solo en tu equipo** (`127.0.0.1`), no en la red. Al entrar a Grafana encontrarás ya cargado el panel **ANVIORA · Operación** (carpeta *ANVIORA*), con: estado de cada servicio, peticiones por segundo, errores 5xx, latencia p95 y respuestas por código de estado.

Prometheus también trae **3 alertas** (`ops/monitoring/alerts.yml`), visibles en http://localhost:9090/alerts:

| Alerta | Se activa cuando | Severidad |
|---|---|---|
| `ServicioCaido` | un servicio no responde su `/metrics` por más de 1 minuto | crítica |
| `ErroresServidorAltos` | más del 5 % de las respuestas de un servicio son 5xx durante 5 minutos | alta |
| `LatenciaAlta` | la latencia p95 de un servicio supera 2 s durante 5 minutos (RNF-01) | media |

> Estas alertas solo se muestran en Prometheus; no envían correos ni mensajes (eso requeriría agregar Alertmanager, ver sección 8).

Si quieres armar tus propios paneles, estas son las consultas base:

| Qué mide | Consulta (PromQL) |
|---|---|
| Peticiones por segundo, por servicio | `sum by (servicio) (rate(anviora_http_requests_total[1m]))` |
| Porcentaje de errores 5xx | `sum(rate(anviora_http_requests_total{estado=~"5.."}[5m])) / sum(rate(anviora_http_requests_total[5m]))` |
| Latencia p95 (RNF-01: < 2 s) | `histogram_quantile(0.95, sum by (le, servicio) (rate(anviora_http_request_duration_seconds_bucket[5m])))` |
| ¿Algún servicio caído? | En Prometheus → *Status → Targets* (deben estar `UP`) |

---

## 5. Respaldos y recuperación

El contenedor `backup` crea un respaldo de PostgreSQL **cada 24 horas** en la carpeta `backups/` del proyecto (formato `.dump`) y conserva los últimos **7 días**.

**Respaldo manual inmediato:**

```powershell
docker compose exec backup sh -c 'pg_dump -Fc -f /backups/manual_$(date +%Y%m%d_%H%M).dump'
```

**Restaurar un respaldo** (reemplaza `ARCHIVO.dump` por el nombre real):

```powershell
docker compose stop core-api auth-service recommendation-service
docker compose cp backups/ARCHIVO.dump db:/tmp/restaurar.dump
docker compose exec db sh -c 'pg_restore -U $POSTGRES_USER -d $POSTGRES_DB --clean --if-exists /tmp/restaurar.dump'
docker compose start core-api auth-service recommendation-service
```

> **Importante:** un respaldo que nunca se probó no es un respaldo. Haz una restauración de prueba al menos una vez. Además, copia la carpeta `backups/` fuera de tu equipo (nube, disco externo): si el disco falla, los respaldos locales también se pierden.

---

## 6. Guía de incidentes (runbook)

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| La página no abre en `localhost:8000` | El gateway no está arriba | `docker compose ps`; luego `docker compose logs gateway` |
| Error **502** en `/api/...` | Un microservicio caído o reiniciándose | `docker compose ps` para ver cuál está `unhealthy`; `docker compose logs <servicio>`; si sigue mal, `docker compose restart <servicio>` |
| Todos los servicios con errores de base de datos | PostgreSQL caído o clave incorrecta | `docker compose logs db`; verifica `POSTGRES_PASSWORD` en `.env` (si la cambiaste después de crear el volumen, la base conserva la clave anterior) |
| `analysis-service` en **503** en `/ready` | El modelo aún está cargando o no se pudo descargar | Espera unos minutos; revisa `docker compose logs analysis-service` (¿hay internet para descargar el modelo?) |
| El análisis de un registro queda en estado `error` | `analysis-service` no respondió | Revisa su salud. El registro y sus recomendaciones **no se pierden** (las reglas de estrés y sueño no dependen de la IA); los análisis siguientes funcionan al recuperarse |
| Un registro se guardó pero no hay recomendaciones | `recommendation-service` caído en ese momento | Revisa su salud; el análisis sí quedó guardado |
| `401` en llamadas entre servicios | `INTERNAL_API_KEY` distinta entre servicios | Debe ser la misma en `.env` para todos; reconstruye con `docker compose up -d` |
| Muchos `429` en login | Límite de peticiones del gateway (anti fuerza bruta) | Es esperado ante ráfagas; ajusta `rate` en `gateway/nginx.conf` si es necesario |
| El disco se llena | Respaldos o logs acumulados | Los logs rotan solos; borra respaldos viejos de `backups/` y revisa con `docker system df` |

**Procedimiento general ante una falla:** (1) `docker compose ps` para ubicar el servicio afectado, (2) `docker compose logs --since 10m <servicio>` para ver la causa, (3) reiniciar solo ese servicio, (4) confirmar que vuelve a `healthy`, (5) anotar qué pasó y cómo se resolvió.

---

## 7. Lista de verificación antes de salir a producción

- [ ] Cambiar `JWT_SECRET_KEY`, `INTERNAL_API_KEY`, `POSTGRES_PASSWORD` y `GRAFANA_ADMIN_PASSWORD` por valores largos y aleatorios.
- [ ] `ENVIRONMENT=production` y `CORS_ORIGINS` con el dominio real (no `*`).
- [ ] Poner HTTPS delante del gateway (certificado TLS con un proxy como Caddy, Traefik o Nginx con Let's Encrypt).
- [ ] No usar `docker-compose.dev.yml`: solo el puerto del gateway debe estar expuesto.
- [ ] No exponer Prometheus ni Grafana a internet sin autenticación.
- [ ] Probar una restauración de respaldo y copiar `backups/` fuera del servidor.
- [ ] Mantener visible el aviso legal: ANVIORA no es un dispositivo médico ni reemplaza la atención profesional.

---

## 8. Limitaciones conocidas y mejoras futuras

- **Base de datos compartida.** Por simplicidad, los servicios comparten un solo PostgreSQL. La separación ideal es una base por servicio, con comunicación solo por API o eventos.
- **Procesamiento en segundo plano dentro de `core-api`.** Usa `BackgroundTasks`: si el contenedor se reinicia en mitad de un análisis, ese registro queda en `procesando`. Una cola de mensajes (Redis/RabbitMQ) con reintentos lo resolvería.
- **JWT sin revocación.** El cierre de sesión solo descarta el token en el cliente.
- **Alertas sin notificación.** Las reglas existen y se ven en Prometheus, pero nadie recibe un correo o mensaje si se activan; faltaría agregar Alertmanager.
- **Un solo servidor.** Docker Compose no escala entre varias máquinas; para eso se usaría Kubernetes u orquestadores similares.

---

## 9. Pruebas

Cada servicio tiene sus pruebas unitarias. Desde la carpeta del servicio:

```powershell
cd services/core-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
```

Para `analysis-service` las pruebas no cargan el modelo real; puedes instalar sus dependencias sin `pysentimiento` si solo quieres correr las pruebas.
