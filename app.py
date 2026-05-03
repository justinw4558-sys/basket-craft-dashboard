import os
import streamlit as st
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Basket Craft — Merchandising Dashboard", layout="wide")
st.title("Basket Craft — Merchandising Dashboard")

# CREATED_AT is stored as nanoseconds since epoch.
# Use TS(col) to convert to a TIMESTAMP anywhere you need date logic.
TS = "TO_TIMESTAMP_NTZ(CREATED_AT / 1000000000)"

# ── Connection ────────────────────────────────────────────────────────────────

@st.cache_resource
def get_conn():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="RAW",
    )


@st.cache_data(ttl=600)
def query(sql: str) -> pd.DataFrame:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    return pd.DataFrame(cur.fetchall(), columns=cols)


# ── Smoke test ────────────────────────────────────────────────────────────────

products_count = query("SELECT COUNT(*) AS N FROM RAW.products").iloc[0, 0]

# ── Sidebar: date filter ───────────────────────────────────────────────────────

min_max = query(f"""
    SELECT
        TO_CHAR(TO_TIMESTAMP_NTZ(MIN(CREATED_AT) / 1000000000), 'YYYY-MM-DD'),
        TO_CHAR(TO_TIMESTAMP_NTZ(MAX(CREATED_AT) / 1000000000), 'YYYY-MM-DD')
    FROM RAW.orders
""")
min_date = pd.to_datetime(min_max.iloc[0, 0]).date()
max_date = pd.to_datetime(min_max.iloc[0, 1]).date()

st.sidebar.header("Date Range")
start_date = st.sidebar.date_input("Start", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End", value=max_date, min_value=min_date, max_value=max_date)

# ── Step 02: KPI Scorecards ───────────────────────────────────────────────────

kpi_sql = f"""
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', {TS})              AS month,
        SUM(PRICE_USD)                         AS revenue,
        COUNT(DISTINCT ORDER_ID)               AS orders,
        SUM(PRICE_USD) / COUNT(DISTINCT ORDER_ID) AS aov,
        SUM(ITEMS_PURCHASED)                   AS items
    FROM RAW.orders
    GROUP BY 1
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY month DESC) AS rn
    FROM monthly
)
SELECT
    MAX(CASE WHEN rn = 1 THEN revenue END) AS cur_revenue,
    MAX(CASE WHEN rn = 2 THEN revenue END) AS prev_revenue,
    MAX(CASE WHEN rn = 1 THEN orders  END) AS cur_orders,
    MAX(CASE WHEN rn = 2 THEN orders  END) AS prev_orders,
    MAX(CASE WHEN rn = 1 THEN aov     END) AS cur_aov,
    MAX(CASE WHEN rn = 2 THEN aov     END) AS prev_aov,
    MAX(CASE WHEN rn = 1 THEN items   END) AS cur_items,
    MAX(CASE WHEN rn = 2 THEN items   END) AS prev_items
FROM ranked
WHERE rn <= 2
"""

kpi = query(kpi_sql).iloc[0]


def delta_pct(cur, prev):
    if prev and prev != 0:
        return (cur - prev) / prev
    return 0.0


col1, col2, col3, col4 = st.columns(4)
col1.metric("Revenue", f"${kpi['CUR_REVENUE']:,.0f}", f"{delta_pct(kpi['CUR_REVENUE'], kpi['PREV_REVENUE']):.1%}")
col2.metric("Orders", f"{kpi['CUR_ORDERS']:,.0f}", f"{delta_pct(kpi['CUR_ORDERS'], kpi['PREV_ORDERS']):.1%}")
col3.metric("Avg Order Value", f"${kpi['CUR_AOV']:,.2f}", f"{delta_pct(kpi['CUR_AOV'], kpi['PREV_AOV']):.1%}")
col4.metric("Items Sold", f"{kpi['CUR_ITEMS']:,.0f}", f"{delta_pct(kpi['CUR_ITEMS'], kpi['PREV_ITEMS']):.1%}")

# ── Step 03: Revenue Trend ────────────────────────────────────────────────────

trend_sql = f"""
SELECT
    TO_DATE(DATE_TRUNC('month', {TS})) AS month,
    SUM(PRICE_USD)                     AS revenue
FROM RAW.orders
WHERE TO_DATE({TS}) BETWEEN '{start_date}' AND '{end_date}'
GROUP BY 1
ORDER BY 1
"""

trend_df = query(trend_sql)
trend_df.columns = trend_df.columns.str.lower()
trend_df["month"] = pd.to_datetime(trend_df["month"])

st.subheader("Revenue Trend")
st.line_chart(trend_df.set_index("month")["revenue"])

# ── Step 04: Top Products by Revenue ─────────────────────────────────────────

top_sql = f"""
SELECT
    p.PRODUCT_NAME,
    SUM(oi.PRICE_USD) AS revenue
FROM RAW.order_items oi
JOIN RAW.products    p  ON p.PRODUCT_ID = oi.PRODUCT_ID
JOIN RAW.orders      o  ON o.ORDER_ID   = oi.ORDER_ID
WHERE TO_DATE(TO_TIMESTAMP_NTZ(o.CREATED_AT / 1000000000)) BETWEEN '{start_date}' AND '{end_date}'
GROUP BY 1
ORDER BY 2 DESC
"""

top_df = query(top_sql)
top_df.columns = top_df.columns.str.lower()

st.subheader("Top Products by Revenue")
st.bar_chart(top_df.set_index("product_name")["revenue"])

# ── Step 05: Bundle Finder ────────────────────────────────────────────────────

all_products = query("SELECT PRODUCT_NAME FROM RAW.products ORDER BY PRODUCT_NAME")
product_names = all_products["PRODUCT_NAME"].tolist()

st.subheader("Bundle Finder: Bought With…")
selected = st.selectbox("Pick a product", product_names)

bundle_sql = f"""
SELECT
    p2.PRODUCT_NAME AS also_bought,
    COUNT(*)        AS order_count
FROM RAW.order_items oi1
JOIN RAW.products    p1  ON p1.PRODUCT_ID = oi1.PRODUCT_ID AND p1.PRODUCT_NAME = '{selected}'
JOIN RAW.order_items oi2 ON oi2.ORDER_ID  = oi1.ORDER_ID   AND oi2.PRODUCT_ID <> oi1.PRODUCT_ID
JOIN RAW.products    p2  ON p2.PRODUCT_ID = oi2.PRODUCT_ID
GROUP BY 1
ORDER BY 2 DESC
"""

bundle_df = query(bundle_sql)
bundle_df.columns = bundle_df.columns.str.lower()

if bundle_df.empty:
    st.info("No co-purchase data found for this product.")
else:
    st.dataframe(bundle_df, use_container_width=True, hide_index=True)
    csv = bundle_df.to_csv(index=False).encode()
    st.download_button(
        "Download CSV",
        csv,
        file_name=f"bundles_{selected.replace(' ', '_')}.csv",
        mime="text/csv",
    )

st.caption(f"Products in catalog: {products_count}")
