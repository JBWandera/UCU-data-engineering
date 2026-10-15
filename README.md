# UCU Data Engineering — Simple ETL Pipeline

Practical assignment: extract branch sales data, clean it with Python, load it into simulated cloud storage, and analyse it with SQL (SQLite).

## Run

```bash
pip install pandas
python etl_pipeline.py
```

The script recreates `cloud_storage_bucket/`, `sales.db` and `query_outputs/` on each run.

## Deliverables

| # | Deliverable | File |
|---|---|---|
| i | Python script | [`etl_pipeline.py`](etl_pipeline.py) |
| ii | Cleaned CSV | [`cloud_storage_bucket/sales/2026/cleaned_sales.csv`](cloud_storage_bucket/sales/2026/cleaned_sales.csv) |
| iii | SQL script | [`sales_analytics.sql`](sales_analytics.sql) |
| iv | Query output exports | [`query_outputs/`](query_outputs/) |
| v | Short explanation | [`REPORT.md`](REPORT.md) |

Raw input: [`sales.csv`](sales.csv), the dataset provided with the assignment.

## Layout

```
sales.csv                      raw input (unchanged)
etl_pipeline.py                Part A transform, Part B load, Part C analytics
sales_analytics.sql            table DDL + 4 analytics queries
cloud_storage_bucket/
  sales/2026/cleaned_sales.csv cleaned data, stored as an object-storage-style key
query_outputs/                 one CSV per query
REPORT.md                      ETL process, challenges, cloud mapping
```
