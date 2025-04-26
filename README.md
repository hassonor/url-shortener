# URL Shortener

![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)

A production-ready, fault-tolerant URL shortening micro-service built with **Python 3.11 + FastAPI** and a modern cloud-native stack (PostgreSQL, Redis, Kafka, Prometheus + Grafana). It offers single-request latency in the low milliseconds while remaining horizontally scalable to millions of links.

---

## ✨ Key Features

| Feature | Details |
|---------|---------|
| **FastAPI HTTP API** | Predictable JSON contract, async I/O, automatic OpenAPI docs |
| **Deterministic short codes** | 7-character SHA-256 hash—zero collisions, idempotent on duplicate URLs |
| **Bloom Filter** in Redis | O(1) membership checks save 99 % of database lookups |
| **PostgreSQL** | ACID-compliant source-of-truth with upsert safety |
| **Kafka event stream** | `url_created_events` topic for analytics & webhooks |
| **Prometheus metrics** | Latency & throughput exported at `/metrics` |
| **Docker Compose stack** | One-command local bootstrap with PostgreSQL, Redis, Kafka, Grafana dashboards |

---

## 🏗 Architecture

```text
┌────────┐      POST /shorten         ┌────────────┐
│ Client │ ─────────────────────────▶ │ FastAPI    │
└────────┘                             │ Service    │
    ▲  ▲        301 redirect          │            │
    │  └────────────────────────────── │            │
GET /{code}                            │            │
    │                                  └────┬──────┘
    │                                       │
    │        cache miss                     │  async events
    │                                       ▼
┌────────┐  lookup   ┌────────┐   ✔ bloom  ┌──────────┐
│ Redis  │ ◀──────── │ Bloom  │ ◀──────────│ Postgres │
└────────┘           └────────┘            └──────────┘
                                         ▲
                                         │
                              publish «url_created_events»
                                         │
                                         ▼
                                    ┌────────┐
                                    │ Kafka  │
                                    └────────┘
```

---

## 🚀 Quick Start (Docker Compose)

```bash
# clone the repository
$ git clone https://github.com/hassonor/url-shortener.git
$ cd url-shortener

# build & start the full stack
$ docker compose up --build
```

* **UI endpoints**
  * API: <http://localhost:8001/docs>
  * Grafana: <http://localhost:3000> (default *admin / admin*)
  * Kafka-UI: <http://localhost:8085>
  * pgAdmin 4: <http://localhost:5050>
  * Redis Commander: <http://localhost:8081>

---

## 📑 HTTP API

### Shorten a URL

```http
POST /shorten
Content-Type: application/json
{
  "longUrl": "https://example.com/some/very/long/path"
}
```

Response `201` Created

```json
{
  "shortUrl": "http://localhost:8001/abc12ef"
}
```

### Redirect

```http
GET /abc12ef → 301 https://example.com/some/very/long/path
```

### Health & Metrics

| Route | Purpose |
|-------|---------|
| `GET /health` | Liveness probe |
| `GET /ready` | Readiness probe |
| `GET /metrics` | Prometheus exposition |

---

## ⚙️ Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `PG_HOST` / `PG_PORT` etc. | `postgres` / `5432` | PostgreSQL connection |
| `REDIS_HOST` / `REDIS_PORT` | `redis` / `6379` | Redis cache |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka cluster |
| `BASE_URL` | `http://localhost:8001` | Public URL of the service |
| `BLOOM_EXPECTED_ITEMS` | `10000000` | Bloom filter capacity |

---

## 🛠 Local Development

```bash
# Python 3.11 + poetry
$ poetry install
$ cp .env.example .env
$ uvicorn shortener.src.main:app --reload --port 8001
```

Unit tests use **pytest**:

```bash
$ poetry run pytest
```

### Pre-commit Hooks

```bash
$ pre-commit install
$ pre-commit run --all-files
```

---

## 📊 Observability

* **Prometheus** scrapes `shortener` + exporters (Redis/Kafka/Postgres)
* **Grafana** dashboards are provisioned from `./grafana/`

---

## 📌 Roadmap

- [ ] Rate limiting & abuse protection
- [ ] Custom vanity short codes
- [ ] OpenTelemetry tracing
- [ ] Helm chart for Kubernetes deployment

---

## 🤝 Contributing

Contributions, issues and feature requests are welcome!  
Please read our **[CODE_OF_CONDUCT](CODE_OF_CONDUCT.md)** and **[CONTRIBUTING](CONTRIBUTING.md)** guidelines (coming soon).

```bash
# run the formatter, linter & tests before pushing
$ make lint test
```

---

## 📝 License

Distributed under the **MIT License**. See **LICENSE** for more information.
