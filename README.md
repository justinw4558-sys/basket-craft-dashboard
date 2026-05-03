# Basket Craft — Merchandising Dashboard

**Live app:** https://basket-craft-dashboard-ra4vfzsrei6evy5dzkacfq.streamlit.app/

A Streamlit dashboard built on the Basket Craft Snowflake data warehouse for Maya, Head of Merchandising. Answers her core questions: which products drive revenue, and which get bought together?

## Features

- **KPI Scorecards** — Revenue, Orders, Average Order Value, and Items Sold with month-over-month deltas
- **Revenue Trend** — Line chart filterable by date range
- **Top Products by Revenue** — Bar chart ranked by revenue, respects date filter
- **Bundle Finder** — Pick a product, see what's bought with it most often; downloadable as CSV

## Setup (local)

1. Clone the repo
2. Copy your Snowflake credentials into `.env` (see `.env` format below)
3. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Run:
   ```bash
   streamlit run app.py
   ```

### `.env` format

```
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=ACCOUNTADMIN
SNOWFLAKE_WAREHOUSE=basket_craft_wh
SNOWFLAKE_DATABASE=basket_craft
SNOWFLAKE_SCHEMA=RAW
```

> `.env` is gitignored and must never be committed.
