# Supply Chain Optimization and Inventory Forecasting System

A Python + FastAPI + MySQL project for inventory decision support. It summarizes demand and supplier performance, calculates transparent reorder-point estimates, provides a simple moving-average forecast baseline, and flags possible shortage/excess risks. It does **not** automatically create purchase orders.

## Features

- REST APIs for products, suppliers, purchase orders, stock transactions, and demand records.
- Inventory report with current stock, average daily demand, estimated safety stock, calculated reorder point, and suggested order quantity.
- Supplier delivery report with actual lead time and on-time delivery rate.
- Demand trend endpoint and baseline forecast endpoint.
- Streamlit dashboard, charts, and CSV download.
- Docker Compose stack for MySQL, API, and dashboard.
- Demo data generator and tests.

## Folder map

- `app/api/routes/`: API endpoints
- `app/db/`: SQLAlchemy models and database connection
- `app/services/`: inventory, demand, supplier, and forecast calculations
- `dashboard/`: Streamlit UI
- `scripts/seed_data.py`: synthetic demonstration dataset
- `tests/`: basic automated tests
- `sql/schema.sql`: reference MySQL schema

## Calculation assumptions

1. **Current stock** = sum of `receipt` and `adjustment_in` quantities minus `sale` and `adjustment_out` quantities. Transaction quantities are entered as positive integers.
2. **Average daily demand** = total demand recorded in the selected lookback window divided by the number of calendar days in that window. Missing dates are treated as zero demand.
3. **Estimated reorder point** = `ceil(average daily demand × lead_time_days + average daily demand × safety_stock_days)`.
4. Default safety stock is 7 days and can be changed per inventory-report request. The formula is a simplified policy, not a statistically optimized service-level model.
5. **Suggested order quantity** = `max(0, calculated reorder point − current stock)`. It does not net out open purchase orders, minimum order quantities, pack sizes, or supplier constraints; review these before making a purchasing decision.
6. **Shortage risk** is flagged when current stock is at or below the calculated reorder point. **Excess risk** is a heuristic flag when stock exceeds demand over lead time + safety-stock days + 60 additional days. These are warnings, not guarantees.
7. The forecast is a transparent moving-average baseline: recent average daily demand multiplied by the forecast horizon. It is not a trained ML model. Compare it with a chronological holdout and a naïve baseline before using operationally.
8. Supplier on-time delivery rate is computed only for received orders that have an expected date. Actual lead time is received date minus order date.

## Option A — Run with Docker (recommended)

Prerequisites: install Docker Desktop and make sure Docker Compose is available.

1. Extract/open this folder in your terminal.
2. Create a local environment file:

   ```bash
   cp .env.example .env
   ```

   On Windows PowerShell, use `Copy-Item .env.example .env`.
3. For a local demo, the example credentials work. Change them before sharing or deploying the application publicly.
4. Start the services:

   ```bash
   docker compose up --build -d
   ```
5. Insert demo data:

   ```bash
   docker compose exec api python -m scripts.seed_data
   ```
6. Open the API documentation at <http://localhost:8000/docs> and dashboard at <http://localhost:8501>.
7. Check service health at <http://localhost:8000/health>.
8. Stop services with `docker compose down`. To also delete the local database volume, use `docker compose down -v` (this permanently deletes the database data).

## Option B — Run locally without Docker

Prerequisites: Python 3.11+ and a running MySQL 8 instance. Create a database and account, then update `.env` with a `DATABASE_URL` such as:

```text
DATABASE_URL=mysql+pymysql://supply_user:supply_password@localhost:3306/supply_chain
API_BASE_URL=http://localhost:8000
SAFETY_STOCK_DAYS=7
```

Commands from the project root:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In a second terminal with the same virtual environment active, seed demo data:

```bash
python -m scripts.seed_data
```

In a third terminal, launch the dashboard:

```bash
streamlit run dashboard/app.py
```

## API quick reference

All API paths below use prefix `/api/v1`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET, POST | `/products` | List/create products |
| GET, DELETE | `/products/{product_id}` | Retrieve/delete a product |
| GET, POST | `/suppliers` | List/create suppliers |
| GET | `/suppliers/{supplier_id}` | Retrieve a supplier |
| GET, POST | `/purchase-orders` | List/create purchase orders |
| GET, POST | `/stock-transactions` | List/create stock movements |
| GET, POST | `/demand-records` | List/create demand records |
| GET | `/analytics/inventory` | Reorder calculations and risk flags |
| GET | `/analytics/demand?product_id=1&days=90` | Demand history summary |
| GET | `/analytics/forecast/1?days=30` | Baseline demand forecast |
| GET | `/analytics/suppliers` | Supplier delivery summary |

Example product request:

```bash
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{"sku":"SKU-2001","product_name":"HDMI Cable","unit_cost":4.5,"lead_time_days":8,"reorder_point":25}'
```

Use `/docs` for interactive requests and response schemas. Stock transaction types are `receipt`, `sale`, `adjustment_in`, and `adjustment_out`; quantity must be positive. Demand records are separate from stock movements and should be supplied as actual demand data. Demo data is synthetic.

## Run tests

With the virtual environment activated and dependencies installed:

```bash
pytest -q
```

Tests use the configured database URL. For an isolated local test run, set `DATABASE_URL=sqlite:///./test_supply_chain.db` before running pytest.

## Push to GitHub

1. Create an empty repository on GitHub, for example `supply-chain-optimization`. Do not initialize it with a README if you already have this one.
2. From the project root, run:

   ```bash
   git init
   git add .
   git commit -m "Build supply chain optimization system"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/supply-chain-optimization.git
   git push -u origin main
   ```

3. Replace `YOUR-USERNAME` with your GitHub username. Authenticate using GitHub's browser sign-in or credential manager when prompted; never put a password or token into source code.
4. For future changes:

   ```bash
   git add .
   git commit -m "Describe your changes"
   git push
   ```

Before pushing, check `git status` and confirm `.env` is not listed. `.gitignore` excludes it. Do not commit real credentials or customer/supplier private data.

## Limitations and future improvements

- Add authentication, role-based permissions, migrations (Alembic), pagination, and audit logging before production use.
- Add a product-to-supplier relationship and purchase-order line items to track quantities by SKU and open-order supply.
- Improve forecast evaluation with rolling-origin validation, MAE/RMSE, and a naïve baseline; only add advanced models when enough historical data exists.
- Calibrate safety stock using demand and lead-time variability and a chosen service level.
- Add timezone, currency, unit-of-measure, data-retention, and monitoring policies for a real deployment.

## Inventory forecasting details

The forecasting endpoint returns a daily history series, a future forecast series, and a chronological holdout comparison. The forecast uses a trailing 7-day moving average (or fewer days when history is shorter) multiplied across the selected horizon. Evaluation compares trailing moving-average predictions with a previous-day naive baseline over the final chronological holdout window. MAE and RMSE are reported for both; lower values indicate smaller errors. This evaluation is descriptive and should be rerun with representative, cleaned business data before operational decisions.

Example: `GET /api/v1/analytics/forecast/1?days=30&history_days=90`.

The dashboard includes forecast horizon and historical-window controls, a chart combining historical demand with projected demand, error metrics, and a JSON download. All forecasts are decision-support estimates; they never trigger automatic purchasing.
