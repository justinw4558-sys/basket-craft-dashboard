# Lesson 10: Streamlit Dashboard Tutorial

In-class today (Wed Apr 29): build and deploy a public Streamlit dashboard against your basket_craft Snowflake mart. Steps 00–06. Goal: leave class with a public Streamlit Community Cloud URL.

**Before class:** confirm your MP02 Snowflake account is still active and you can query the basket_craft `analytics` schema. Throughout this tutorial you ask Claude Code to do things. It handles the venv, the installs, `git`, `streamlit run`. You describe what you want; the agent runs it.

## What is Streamlit?

[Streamlit](https://streamlit.io) is an open-source Python framework that turns a Python script into an interactive web app. No JavaScript, no separate front end, no templates. You write Python; Streamlit handles the HTML, widgets, and rendering. For data dashboards on top of a warehouse, it's the fastest path from a SQL query to something a stakeholder can click. Today you'll end up with a public URL anyone can visit, hosted on Streamlit Community Cloud (free tier), backed by your basket_craft mart in Snowflake.

## Table of Contents

| Step | Topic | What You Will Do |
|------|-------|-----------------|
| 00 | [Set up the project](#step-00-set-up-the-project) | Repo, `.env` with Snowflake credentials, sign up for Streamlit Community Cloud |
| 01 | [Connect to Snowflake](#step-01-connect-to-snowflake) | Ask Claude Code to build the dashboard; verify the connection works |
| 02 | [Descriptive: KPI scorecards](#step-02-descriptive-kpi-scorecards) | Headline metrics with month-over-month change |
| 03 | [Descriptive: Revenue trend](#step-03-descriptive-revenue-trend) | Trend over time with a date filter |
| 04 | [Diagnostic: Top products by revenue](#step-04-diagnostic-top-products-by-revenue) | Which products are driving the numbers |
| 05 | [Diagnostic and Act: Bundle finder](#step-05-diagnostic-and-act-bundle-finder) | Pick a product, see what's bought with it |
| 06 | [Deploy to Streamlit Community Cloud](#step-06-deploy-to-streamlit-community-cloud) | Public URL |

---

## Part 01: Setup

### Step 00: Set Up the Project

Same opening move as MP02 through MP04. New repo on GitHub, clone in Cursor, drop your Snowflake credentials in `.env`, sign up for Streamlit Cloud. No Claude Code yet. That comes in Step 01.

**What to do:**

1. Go to [github.com/new](https://github.com/new) and create a new repository:

   - Name it `basket-craft-dashboard`
   - Set visibility to **Public**
   - Under **Add .gitignore**, select **Python** from the dropdown
   - Leave everything else as default
   - Click **Create repository**

2. Clone it into Cursor next to your other ISBA repos:

   ```
   ~/isba-4715/
   ├── basket-craft-pipeline/    <-- MP02
   ├── weather-api-pipeline/     <-- MP03
   ├── chipotle-scrape-pipeline/ <-- MP04
   └── basket-craft-dashboard/   <-- LE10
   ```

3. **Sign up for Streamlit Community Cloud** at [streamlit.io/cloud](https://streamlit.io/cloud) using GitHub OAuth. Free tier is fine; unlimited public apps. We deploy here in Step 06.

4. Copy and paste your Snowflake credentials from the `.env` file in your `basket-craft-pipeline` repo (MP02). Save them as `.env` at the root of this repo.

   The Python `.gitignore` template you picked already excludes `.env`, so this file won't be committed. Verify with the file explorer in Cursor. `.env` should appear greyed out.

**Account format gotcha.** Your account identifier must use hyphens (`xy12345-abc6789`), not underscores. Same form your MP02 loader needed.

**Looking ahead.** Snowflake is rolling out mandatory MFA for password users in phases through August 2026. Password auth still works for the rest of the semester. After August, migrate to key-pair auth for any production use.

**Checkpoint:** Repo cloned, `.env` populated with all seven Snowflake values, signed in to Streamlit Community Cloud.

---

### Step 01: Connect to Snowflake

Two narrow prompts: one to set up an empty dashboard, one to add the Snowflake connection. Each prompt is focused enough that the agent doesn't have a full design to brainstorm about.

**What to do:**

1. Open a terminal in Cursor and start Claude Code:

   ```bash
   claude
   ```

2. Set up an empty dashboard. Paste:

   ```
   Set up an empty Streamlit dashboard. Get my Python environment
   ready, create a minimal app file with just a title, and run it.
   ```

   Claude Code installs packages, creates the app file, and prints a local URL. Click it. You should see a mostly empty Streamlit page with just a title. That's the proof that setup works.

3. Add the Snowflake connection. Paste:

   ```
   Connect this dashboard to my Snowflake data warehouse using the
   credentials in .env. Add a smoke-test query that shows a row count
   from one of my dimension tables. Cache the query.
   ```

   Claude Code reads `.env`, wires up the connection, and adds a cached smoke-test query. Rerun the dashboard. You should see a single number, a row count from one of your dimensions.

4. Click **Rerun** in the Streamlit menu (top-right of the page). The first run took 2–5 seconds (Snowflake round-trip); the rerun is instant. That's caching kicking in.

**If the brainstorming skill kicks in anyway.** Superpowers' brainstorming skill triggers on open-ended prompts ("help me design...", "what should we build..."). The two prompts above are narrow enough that it usually stays out of the way. If it kicks in regardless and starts asking design questions, you have three options, in order of preference:

- **Press Esc** to interrupt Claude Code mid-response, then paste a more specific prompt.
- **Tell it to skip:** *"Skip the brainstorm. Just do exactly what I asked."*
- **Cancel and re-prompt:** Ctrl+C in the terminal cancels the current request; you can paste a tighter version.

Reserve brainstorming for moments you genuinely need to clarify (a missing column name, an unfamiliar dimension), not as the default for every prompt.

**Why caching matters.** Every Streamlit interaction (slider, button, dropdown) re-runs your script top to bottom. Without caching, every interaction re-queries Snowflake. With caching, results are reused until inputs change. For a dashboard with four charts plus a filter, caching is the difference between snappy and sluggish.

**Heads-up on Python version.** `snowflake-snowpark-python` doesn't yet support Python 3.12 or 3.13. If your machine is on a newer Python, Claude Code will install Python 3.11 with pyenv as part of the setup.

**Troubleshooting.** If the app errors instead of showing a row count:
- Connection error → check `.env`, account format must use hyphens, no quotes around values
- Object doesn't exist → wrong database/schema/role in `.env`, or the table name Claude Code guessed doesn't match yours. Tell Claude Code your actual table name.

**Checkpoint:** the local Streamlit URL shows a row count; rerun is instant.

---

## Part 02: Build the Dashboard for Maya

Maya, the Head of Merchandising at Basket Craft, is your stakeholder. The dbt mart you built in MP02 Step 25 was designed around her questions:

- Which products drove the most revenue each month last quarter?
- Which products get bought together most often? Should we create bundles?
- Which products have the highest refund rates?
- Do new customers buy different products than customers who've been with us for a while?

The dashboard answers her first two questions directly. KPIs and trend chart give her the headline; the product bar chart shows what's selling; the bundle finder surfaces co-purchase patterns she can use to design bundles.

```
┌──────────────────────────────────────────────────────────────────────┐
│ Basket Craft — Merchandising Dashboard                               │
├──────────────┬───────────────────────────────────────────────────────┤
│              │ ┌──────────┬──────────┬──────────┬──────────┐         │
│  Date range  │ │ Revenue  │  Orders  │   AOV    │  Items   │ Step 02 │
│              │ │ $129K ▼2%│ 2,064 ▼2%│ $62  ▼1% │ 2,701 ▼5%│         │
│  ┌────────┐  │ └──────────┴──────────┴──────────┴──────────┘         │
│  │ start  │  │                                                       │
│  │ end    │  │ Revenue Trend                                  Step 03│
│  └────────┘  │     ╱╲    ╱╲╱╲                                        │
│              │    ╱  ╲  ╱    ╲      ╱╲                               │
│              │   ╱    ╲╱      ╲    ╱  ╲                              │
│              │  ╱                ╲╱    ╲                             │
│              │  2024              2025          2026                 │
│              │                                                       │
│              │ Top Products by Revenue                        Step 04│
│              │ ████████████████  The Original Gift Basket            │
│              │ █████             The Valentine's Gift Basket         │
│              │ ███               The Birthday Gift Basket            │
│              │ ██                The Holiday Gift Basket             │
│              │                                                       │
│              │ Bundle Finder: Bought With…                    Step 05│
│              │ Pick a product: ▾  The Original Gift Basket           │
│              │ ┌────────────────────────────┬──────────────┐         │
│              │ │ Also bought                │ # of orders  │         │
│              │ │ The Holiday Gift Basket    │ 3,142        │ ⬇ CSV   │
│              │ │ The Birthday Gift Basket   │ 2,036        │         │
│              │ │ The Valentine's Gift Basket│ 944          │         │
│              │ └────────────────────────────┴──────────────┘         │
└──────────────┴───────────────────────────────────────────────────────┘
```

**Reading top to bottom:** what's happening overall (KPIs) → how revenue moved over time (trend) → which products are driving it (top products) → which products go together (bundle finder). Descriptive at top, diagnostic in the middle, actionable at the bottom. The bundle finder is downloadable CSV; that's what Maya hands to a buyer to design promotions.

**You own the numbers.** Claude Code generates SQL that looks right but isn't always right. Wrong joins, mis-applied filters, off-by-one date boundaries — every one of these produces *a* number, just not the right one. Before trusting any chart, sanity-check the result with a quick SQL query directly in Snowsight: pull the same total a different way and confirm the dashboard agrees. If the numbers disagree, paste the discrepancy back to Claude Code and have it explain. The dashboard is your work, not the agent's. A bad number Maya makes a decision on is a bad merchandising call with your name on it.

### Step 02: Descriptive — KPI Scorecards

KPIs answer "where are we now?" in thirty seconds. They're the headline numbers a Head of Merchandising scans before drilling into the rest.

**What to do:**

1. Paste this:

   ```
   Add headline metrics to my dashboard: total revenue, total orders,
   average order value, and total items sold. Each should show how
   it changed versus the prior month.
   ```

2. Ask Claude Code to rerun the dashboard. You should see four metric cards across the top, each with a number and a green or red delta percentage.

**Why these four?** Revenue, orders, AOV, and items sold are the volume-and-value pair Maya scans first. Items Sold is line-item level (`fct_order_items`), distinct from order count. A customer who orders once with five items contributes one order but five items. Both numbers matter to a merchandising lead.

**Checkpoint:** Four metric cards visible with current values and MoM deltas.

---

### Step 03: Descriptive — Revenue Trend

The KPIs answered "where are we now?" The trend chart answers "how did we get here?"

**What to do:**

1. Paste this:

   ```
   Add a revenue trend over time to my dashboard, and let me filter
   the chart by date range.
   ```

2. Ask Claude Code to rerun. You should see a date filter in the sidebar and a line chart that responds when you change the dates.

3. Try it. Drag the start date forward by six months. The line chart updates. Drag it back. The KPIs above don't change; that's intentional.

**Why the date filter doesn't affect the KPIs.** KPIs answer "current state" (always the latest two months). The trend chart is for *exploring* time windows. Stable KPIs at the top with explorable charts below them is a real production pattern.

**Checkpoint:** Sidebar date filter visible, line chart responds, KPIs unchanged.

---

### Step 04: Diagnostic — Top Products by Revenue

Steps 02 and 03 showed *what's happening*. Step 04 starts answering *which products are driving it*, Maya's first MP02 question.

**What to do:**

1. Paste this:

   ```
   Add a bar chart to my dashboard showing the top products by
   revenue. Have it respect the date filter.
   ```

2. Ask Claude Code to rerun. You should see a bar chart with product names along one axis and revenue along the other, sorted from highest to lowest.

3. Change the sidebar date range to a single quarter or year. The chart re-renders for that window. The relative ranking can shift meaningfully. That's the diagnostic story: a revenue dip in Step 03 might come from one product falling off, and the bar chart shows which.

**About "top products."** Basket Craft's catalog has only four products, so "top products" effectively means all four sorted. If you applied this dashboard to a portfolio mart with hundreds of SKUs, you'd want to limit to the top 10 or 20 to keep the chart readable. Tell Claude Code the cut-off if your catalog is large.

**Checkpoint:** Bar chart of top products by revenue renders below the line chart, sorted descending, and the date filter changes the bars.

---

### Step 05: Diagnostic and Act — Bundle Finder

Maya's second MP02 question: "Which products get bought together most often? Should we create bundles?" The bundle finder answers it directly. Pick a product, see what shows up in the same orders.

**What to do:**

1. Paste this:

   ```
   Add a bundle finder to my dashboard. Let me pick any product, and
   show me the products that get bought together with it most often,
   ranked by how many orders contained both.
   ```

2. Ask Claude Code to rerun. You should see a product dropdown, a table showing other products that appear in the same orders, and a way to download the list.

3. Try the act flow. Pick a product from the dropdown. The table re-renders showing what's bought with it. Hover over the table, click the download icon (top-right), and you get a CSV. That CSV is what Maya hands to a buyer to design a bundle promotion.

**The query underneath.** A product co-purchase view is a self-join: same fact table appears twice in the FROM, once for "the product I picked" and once for "everything else in the same order." Claude Code writes the self-join; you describe the question. If it errors on column names, paste the error back and tell it the right ones.

**Why a table instead of a chart?** Bundles are about specific product pairings, not a rank-ordered visual. Maya wants to see the names. "The Original Gift Basket sells with The Holiday Gift Basket 3,142 times" is the actionable insight. A bar chart of co-purchase counts hides the names.

**Checkpoint:** Product dropdown changes the table, ranked by co-occurrence count, CSV download works.

---

## Part 03: Ship It

### Step 06: Deploy to Streamlit Community Cloud

The dashboard runs locally. Now you push it to a public URL.

**What to do:**

1. Push to GitHub. Paste this:

   ```
   commit and push to GitHub
   ```

2. In your locally running Streamlit app, click the **Deploy** button in the top-right corner of the page.

3. A modal appears titled "Deploy this app using…". Click **Deploy now** under the **Streamlit Community Cloud** card (the leftmost option, "For community, always free"). Streamlit detects your local app's repo and pre-fills the form.

4. Click **Advanced settings**. The Secrets box wants [TOML format](https://toml.io). Same seven values from your `.env`, with quotes and `=` spaces. Paste:

   ```
   SNOWFLAKE_ACCOUNT = "xy12345-abc6789"
   SNOWFLAKE_USER = "your_user"
   SNOWFLAKE_PASSWORD = "your_password"
   SNOWFLAKE_ROLE = "LOADER"
   SNOWFLAKE_WAREHOUSE = "BASKET_CRAFT_WH"
   SNOWFLAKE_DATABASE = "BASKET_CRAFT"
   SNOWFLAKE_SCHEMA = "ANALYTICS"
   ```

   Or ask Claude Code to convert your `.env` for you:

   ```
   Convert my .env values to the TOML format Streamlit Cloud's
   Secrets box expects.
   ```

   Your local `.env` stays gitignored; the Cloud-side text box stores the same values in Streamlit's encrypted backend.

5. Click **Deploy**. The first build takes 60–90 seconds. Watch the log; failures show up there.

6. Once live, test every interactive element: date filter, product dropdown, CSV download. Then ask Claude Code to write a README that pins the URL at the top:

   ```
   Create a README.md with my live Streamlit Cloud URL at the top.
   Commit and push.
   ```

**Common failures:**

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError` on build | Missing or mispinned package in `requirements.txt` |
| Snowflake auth error | Account format (hyphens, not underscores), wrong password, or wrong role |
| Object doesn't exist | Wrong database, schema, or role in Cloud Secrets |
| Build hangs > 3 min on first deploy | Normal; click "Manage app" to watch the live log |

**Checkpoint:** Public Streamlit URL renders all four sections, every interactive element works, README links to the live URL.

---

## Submission

Submit your `basket-craft-dashboard` repo URL and your Streamlit Cloud URL on Brightspace.

Your `basket-craft-dashboard` repo should contain:
- The Streamlit app with all four dashboard sections
- `requirements.txt` with pinned package versions
- `.gitignore` excluding `.env`
- `README.md` with the live Streamlit Cloud URL pinned at the top

It must NOT contain:
- `.env` — must be gitignored, no Snowflake credentials in git history. If you accidentally committed it, rotate the Snowflake password immediately and scrub history.
