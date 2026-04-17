# Personal Chatbot — Case Study 3

## Project Goal
Deploy both Case Study 1 products (API-based chatbot + locally executed product) in Docker containers on a shared VM, add Prometheus monitoring, and expose them publicly via ngrok.

## Deliverables Checklist
- [ ] Docker containers for both products running on shared VM
- [ ] Prometheus node exporter (container-level metrics)
- [ ] Python `prometheus_client` metrics (4–10 per product)
- [ ] Public ngrok URLs for both products
- [ ] Port Tracking Spreadsheet entries (ports + ngrok URLs)
- [ ] 2–3 page project report

## Architecture
- **API-based product**: frontend + backend in Docker, exposed via ngrok
- **Locally executed product**: frontend + backend in Docker, exposed via ngrok
- **Monitoring**: `prometheus-node-exporter` (system metrics) + Python `prometheus_client` (app metrics)
- **Extra credit**: Grafana server in Docker, exposed via ngrok

## Key Ports
Claim ports in the shared VM spreadsheet to avoid conflicts. Document all ports used.

## Monitoring Requirements
Each product must expose 4–10 meaningful Python-level Prometheus metrics (e.g., request count, latency, error rate, active sessions).

## Notes
- Use `docker-compose.yml` to orchestrate services
- Document any changes made from Case Study 1 to make products work in Docker
- Both products must have public URLs — not just one
