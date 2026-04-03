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

Based on Prof. Paffenroth's original CSDS553 Demo chatbot, added changes include:

File upload and context integration
Response time measurement and display

### Running with Docker

---

**Step 1 — Build the image**

```bash
./build.sh
```

Builds the Docker image and tags it as `mlops-group8`.

**Step 2 — Start the containers**

```bash
./run.sh
```

Starts the app and Grafana containers with the following port bindings:

| Service | URL |
|---|---|
| Frontend (Gradio) | http://localhost:22111 |
| Backend (FastAPI) | http://localhost:22112 |
| Grafana | http://localhost:22113 |

**Step 3 — Expose via devtunnel**

Make sure you are logged in first:

```bash
~/bin/devtunnel user login
```

Then start the tunnel:

```bash
./tunnel.sh
```

devtunnel will print public URLs for each port in the terminal.
