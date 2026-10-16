"""
Simple ETL pipeline for branch sales data.

Part A  Extract + Transform : sales.csv -> cleaned_sales.csv
Part B  Load (cloud-like)   : cleaned_sales.csv -> cloud_storage_bucket/sales/2026/
Part C  SQL analytics       : bucket object -> SQLite table `sales` -> query_outputs/*.csv

Run:  python etl_pipeline.py
"""
import shutil
import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
RAW_FILE = BASE / "sales.csv"
CLEAN_FILE = BASE / "cleaned_sales.csv"
BUCKET = BASE / "cloud_storage_bucket"
DB_FILE = BASE / "sales.db"
SQL_FILE = BASE / "sales_analytics.sql"
OUTPUT_DIR = BASE / "query_outputs"

# Branches submit dates in several formats. Every non-ISO format in the data is
# day-first (e.g. 03/01/2026 sits between 2026-01-03 and 2026/01/04), so we parse
# with explicit formats instead of letting pandas guess month/day order.
DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"]

REQUIRED = ["transaction_id", "transaction_date", "quantity", "unit_price"]
TEXT_COLS = ["branch", "product", "category"]


def parse_date(value):
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(value, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.NaT


#  Part A

def extract(path=RAW_FILE):
    # Read every column as text so we decide how bad values are handled.
    df = pd.read_csv(path, dtype=str)
    print(f"[extract] {len(df)} rows read from {path.name}")
    return df


def transform(df):
    df = df.apply(lambda col: col.str.strip())
    log = {"raw_rows": len(df)}

    # i. Duplicates: exact copies first, then any re-used transaction_id (keep first seen).
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="transaction_id", keep="first")
    log["duplicates_removed"] = log["raw_rows"] - len(df)

    # ii. Missing values.
    #   - quantity / unit_price / id / date are needed to compute revenue. Guessing a
    #     missing quantity would invent sales, so those rows are dropped.
    #   - descriptive text fields are kept and labelled "Unknown".
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=REQUIRED)
    log["missing_required_removed"] = before - len(df)
    df[TEXT_COLS] = df[TEXT_COLS].fillna("Unknown")

    # iii. Standardise transaction_date to ISO YYYY-MM-DD; unparseable dates are dropped.
    df["transaction_date"] = df["transaction_date"].map(parse_date)
    before = len(df)
    df = df.dropna(subset=["transaction_date"])
    log["bad_dates_removed"] = before - len(df)
    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")

    # iv. Negative (and zero) quantities are not valid sales.
    before = len(df)
    df = df[df["quantity"] > 0]
    log["non_positive_qty_removed"] = before - len(df)

    df["quantity"] = df["quantity"].astype(int)
    df["unit_price"] = df["unit_price"].astype(int)

    # 3. Derived column
    df["total_amount"] = df["quantity"] * df["unit_price"]

    df = df.sort_values("transaction_id").reset_index(drop=True)
    log["clean_rows"] = len(df)
    for k, v in log.items():
        print(f"[transform] {k}: {v}")
    return df


def validate(df):
    # The load step runs only if all of these checks pass.
    assert df["transaction_id"].is_unique, "duplicate transaction_id"
    assert not df.isna().any().any(), "missing values remain"
    assert (df["quantity"] > 0).all(), "non-positive quantity remains"
    assert (df["total_amount"] == df["quantity"] * df["unit_price"]).all()
    assert df["transaction_date"].str.fullmatch(r"\d{4}-\d{2}-\d{2}").all()
    print("[validate] all checks passed")


#  Part B

def load_to_bucket(clean_file=CLEAN_FILE):
    """
    Simulates object storage (e.g. AWS S3, Azure Blob, Google Cloud Storage):
      - cloud_storage_bucket/      -> the bucket (top-level, uniquely named container)
      - sales/2026/cleaned_sales.csv -> the object KEY. Object stores are flat; the
        "/" separators are a naming convention (prefixes) that consoles display
        as folders. Prefixes like dataset/year/ let query engines and lifecycle rules
        target one slice of the data (partitioning) without scanning everything.
      - The file is written once and never edited; a new run replaces the
        whole object, the same way a PUT to S3 does.
    """
    target_dir = BUCKET / "sales" / "2026"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / clean_file.name
    shutil.move(str(clean_file), target)
    print(f"[load] moved to {target.relative_to(BASE).as_posix()}")
    return target


#  Part C

def read_sql_script(path=SQL_FILE):
    """Split the SQL file into the DDL block and the named analytics queries."""
    chunks = path.read_text(encoding="utf-8").split("-- name:")
    ddl, queries = chunks[0], {}
    for chunk in chunks[1:]:
        name, _, body = chunk.partition("\n")
        # Drop the trailing comment that introduces the next query.
        body = "\n".join(l for l in body.splitlines() if not l.startswith("--"))
        queries[name.strip()] = body.strip().rstrip(";")
    return ddl, queries


def run_analytics(bucket_object):
    ddl, queries = read_sql_script()
    OUTPUT_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        conn.executescript(ddl)  # 1. create table
        pd.read_csv(bucket_object).to_sql("sales", conn, if_exists="append", index=False)  # 2. load
        n = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        print(f"[sql] loaded {n} rows into table `sales` ({DB_FILE.name})")

        for name, sql in queries.items():  # 3 + 4. query and export
            result = pd.read_sql_query(sql, conn)
            result.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
            print(f"\n=== {name} ===")
            print(result.to_string(index=False))


def main():
    raw = extract()
    clean = transform(raw)
    validate(clean)
    clean.to_csv(CLEAN_FILE, index=False)
    print(f"[transform] saved {CLEAN_FILE.name}")
    bucket_object = load_to_bucket()
    run_analytics(bucket_object)


if __name__ == "__main__":
    main()
