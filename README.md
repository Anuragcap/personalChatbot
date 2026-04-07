---
title: PersonalChatbot
emoji: 💬
colorFrom: yellow
colorTo: purple
sdk: gradio
app_file: app.py
pinned: false
hf_oauth: true
hf_oauth_scopes:
  - inference-api
---

Based on Prof. Paffenroth's original CSDS553 Demo chatbot. Added changes include file upload and context integration, response time measurement and display, and a FastAPI backend with Prometheus metrics.

---

### Running with Docker Compose

**Prerequisites:** Docker and Docker Compose installed. Copy `.env.example` to `.env` and set your `HF_TOKEN`.

**Step 1 — Start all services**

```bash
./run.sh
```

Builds `Dockerfile.frontend` and `Dockerfile.backend` (if needed) and starts all containers via `docker compose up -d --build`.

| Service | Local URL |
|---|---|
| Frontend (Gradio) | http://localhost:22111 |
| Backend (FastAPI) | http://localhost:22112 |
| Backend Metrics | http://localhost:22112/metrics |
| Grafana | http://localhost:22117 |
| Node Exporter | http://localhost:22114/metrics |

**Step 2 — Expose via devtunnel**

Make sure you are logged in first:

```bash
~/bin/devtunnel user login
```

Then start the tunnel:

```bash
./tunnel.sh
```

`tunnel.sh` will start the services if they are not already running, then create (or reuse) the `mlops-group8` tunnel and print public URLs for each port.

**Step 3 — Stop everything**

```bash
./stop.sh
```

Runs `docker compose down` and kills any active devtunnel processes.

---

### Architecture

Frontend and backend run in **separate containers** connected via a Docker bridge network named `mlopsgroup8`.

| Container | Image built from | Port mapping | Network |
|---|---|---|---|
| `mlops-group8-frontend` | `Dockerfile.frontend` | 22111 → 7008 | mlopsgroup8 |
| `mlops-group8-backend` | `Dockerfile.backend` | 22112 → 9008 | mlopsgroup8 |
| `group08otel-lgtm` | `grafana/otel-lgtm` | 22117 → 3000 | mlopsgroup8 |
| `mlops-group8-node-exporter` | `prom/node-exporter` | 22114 (host) | host |

- **`frontend.py`** — Gradio UI, listens on port `7008`. Reaches the backend via `http://backend:9008` — Docker DNS on the `mlopsgroup8` network resolves the service name `backend` to the backend container. This is set via `BACKEND_URL=http://backend:9008` in `docker-compose.yml`.
- **`api_backend.py`** — FastAPI backend, listens on port `9008`. Exposes Prometheus metrics at `/metrics`.
- **Node Exporter** uses `network_mode: host` so it can see real host metrics — it is not on the `mlopsgroup8` network and does not need to be.

**Why `http://backend:9008` and not `http://localhost:9008`?**
Each container has its own network namespace. `localhost` inside the frontend container refers to the frontend container itself, not the backend. Docker Compose creates a DNS entry for each service name scoped to the shared network, so `backend` resolves correctly. If another Compose project on the same VM has a service also named `backend` on a different network, there is no conflict — DNS resolution is network-scoped.

**Separate requirements files:**
- `requirements.frontend.txt` — only Gradio, requests, python-dotenv
- `requirements.backend.txt` — FastAPI, uvicorn, prometheus-client, HuggingFace, transformers, torch

---

### Monitoring

#### Container-Level — Node Exporter

Node Exporter runs as a separate container (started automatically) and exposes host-level system metrics.

- **Metrics endpoint:** http://localhost:9100/metrics
- Exposes CPU, memory, disk I/O, network, and filesystem metrics
- Verify: `docker compose ps`

#### Application-Level — Prometheus Python Client

`api_backend.py` uses the `prometheus-client` library to expose 6 custom metrics at `/metrics`.

| Metric | Type | Description |
|---|---|---|
| `chatbot_requests_total` | Counter | Total requests labeled by `status` (success/error) and `model_type` (api/local) |
| `chatbot_errors_total` | Counter | Errors by `error_type` (auth_error, hf_api_error, local_model_error) |
| `chatbot_response_time_seconds` | Histogram | Response time distribution in seconds |
| `chatbot_active_requests` | Gauge | Number of requests currently being processed |
| `chatbot_tokens_requested` | Histogram | Distribution of `max_tokens` values per request |
| `chatbot_history_length` | Histogram | Number of prior messages sent in each request |

- **Metrics endpoint:** http://localhost:22112/metrics
- Verify: `curl http://localhost:22112/metrics`

#### Grafana

Grafana (with OpenTelemetry LGTM stack) runs on port `22113`. Access it at http://localhost:22113 (default credentials: `admin` / `admin`).
