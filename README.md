# Smart Fridge Demand API

A small production-style Python backend for food-tech operations. It stores products and daily sales, exposes REST APIs, calculates operational metrics, and predicts near-term product demand from historical sales.

The project is intentionally compact enough to understand end-to-end while still demonstrating backend structure, database integration, testing, Docker, CI, and a basic predictive-modeling workflow.

> **Data note:** the included seed data is synthetic. This repository does not contain or reproduce data from any employer or third party.

## What it demonstrates

- Python backend development with FastAPI
- REST API design and validation with Pydantic
- SQLAlchemy ORM and relational data modeling
- PostgreSQL in Docker, with SQLite as a local fallback
- Historical sales/data processing with Pandas
- Predictive modeling with scikit-learn
- Business-facing analytics such as demand and waste metrics
- Unit/API tests with pytest
- Docker and Docker Compose
- CI with GitHub Actions

## Architecture

```text
Client
  |
  v
FastAPI routes
  |
  +---- Products / Sales / Analytics
  |             |
  |             v
  |        SQLAlchemy ORM
  |             |
  |             v
  |      PostgreSQL / SQLite
  |
  +---- Forecast endpoint
                |
                v
          Pandas feature prep
                |
                v
       RandomForestRegressor
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health |
| POST | `/api/products` | Create a product |
| GET | `/api/products` | List products |
| POST | `/api/sales` | Store daily product sales |
| GET | `/api/products/{product_id}/analytics` | Demand/waste summary |
| POST | `/api/forecast` | Predict demand for a future date |

FastAPI also exposes interactive documentation at `/docs`.

## Quick start: local Python

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env

python scripts/seed.py
uvicorn app.main:app --reload
```

Open:

- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

By default the project uses SQLite, so PostgreSQL is not required for the quick start.

## Run with PostgreSQL and Docker

```bash
docker compose up --build
```

In another terminal:

```bash
docker compose exec api python scripts/seed.py
```

Then open http://localhost:8000/docs.

## Example forecast request

```bash
curl -X POST "http://127.0.0.1:8000/api/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "target_date": "2026-10-05"
  }'
```

Example response:

```json
{
  "product_id": 1,
  "target_date": "2026-10-05",
  "predicted_demand": 43,
  "training_samples": 83,
  "model": "RandomForestRegressor"
}
```

The exact number depends on the synthetic seed data.

## Forecasting approach

For one product, the service loads historical daily sales and creates simple calendar/time-series features:

- weekday
- month
- 7-day lag
- rolling 7-day average

It trains a `RandomForestRegressor` and returns a non-negative rounded demand prediction.

This is deliberately a simple baseline rather than a claim of production-grade forecasting. In a real food-tech system I would evaluate time-based validation, seasonality, holidays, promotions, office attendance, stock-outs, weather, menu changes, cold-start handling, and forecast error by product/location.

## Run tests

```bash
pytest
```

## Project structure

```text
smart-fridge-demand-api/
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── services/
│   │   └── forecasting.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
├── scripts/
│   └── seed.py
├── tests/
│   └── test_api.py
├── .github/workflows/
│   └── ci.yml
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── requirements.txt
```

## Suggested GitHub repository description

> Python/FastAPI backend for smart-fridge demand forecasting with PostgreSQL, Pandas, scikit-learn, Docker and pytest.

## Possible next improvements

- Alembic database migrations
- Authentication and role-based access
- Per-office/fridge inventory
- Stock-out and replenishment events
- Background model training
- Model versioning and stored metrics
- Time-series cross-validation and MAE/MAPE tracking
- Holiday/weather/office-attendance features
- Angular or TypeScript dashboard
- Odoo integration through a dedicated adapter/API layer
