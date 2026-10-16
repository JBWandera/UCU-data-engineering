-- Part C: SQL Analytics (SQLite)
-- Run by etl_pipeline.py, which creates the table, loads the data, then runs the queries.
-- To run a query by hand, open sales.db in the sqlite3 CLI and paste it (see RUNNING_IN_VSCODE.md).
-- Each query carries a "name" tag; the pipeline exports it to query_outputs/<name>.csv

-- 1. Create the sales table
DROP TABLE IF EXISTS sales;
CREATE TABLE sales (
    transaction_id   TEXT PRIMARY KEY,
    transaction_date DATE    NOT NULL,
    branch           TEXT    NOT NULL,
    product          TEXT    NOT NULL,
    category         TEXT    NOT NULL,
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    unit_price       INTEGER NOT NULL CHECK (unit_price >= 0),
    total_amount     INTEGER NOT NULL
);

-- 2. Load cleaned_sales.csv
-- etl_pipeline.py inserts the rows from cloud_storage_bucket/sales/2026/cleaned_sales.csv.
-- With the sqlite3 CLI the equivalent is:
--   .import --csv --skip 1 cloud_storage_bucket/sales/2026/cleaned_sales.csv sales

-- 3a. Total revenue per branch
-- name: revenue_per_branch
SELECT branch,
       COUNT(*)          AS transactions,
       SUM(total_amount) AS total_revenue
FROM sales
GROUP BY branch
ORDER BY total_revenue DESC;

-- 3b. Total revenue per product category
-- name: revenue_per_category
SELECT category,
       COUNT(*)          AS transactions,
       SUM(total_amount) AS total_revenue
FROM sales
GROUP BY category
ORDER BY total_revenue DESC;

-- 3c. Top 5 products by total sales amount
-- name: top5_products
SELECT product,
       SUM(quantity)     AS units_sold,
       SUM(total_amount) AS total_sales
FROM sales
GROUP BY product
ORDER BY total_sales DESC
LIMIT 5;

-- 3d. Average transaction value
-- name: avg_transaction_value
SELECT COUNT(*)                    AS transactions,
       ROUND(AVG(total_amount), 2) AS avg_transaction_value
FROM sales;
