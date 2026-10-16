# Running the Pipeline in VS Code

This guide takes you from a fresh Windows laptop to a full pipeline run in VS Code. A run takes a few seconds and rebuilds every output file in the project.

## 1. Install the tools (once)

1. **Python 3.10 or newer** from https://www.python.org/downloads/. On the first installer screen, tick **"Add python.exe to PATH"** before clicking Install.
2. **VS Code** from https://code.visualstudio.com/.
3. **Git** from https://git-scm.com/downloads, if you want to clone the repo rather than download it.
4. In VS Code, open the Extensions panel (`Ctrl+Shift+X`) and install **Python** (publisher: Microsoft).

To check that Python is installed, open a new terminal and run:

```bash
python --version
```

If you get `Python was not found; run without arguments to install from the Microsoft Store`, Windows is running its Store shortcut instead of the real Python. Open **Settings → Apps → Advanced app settings → App execution aliases**, switch off both `python.exe` and `python3.exe`, then open a new terminal and try again.

## 2. Get the project

Clone it:

```bash
git clone https://github.com/JBWandera/UCU-data-engineering
```

Or, on the GitHub page, click **Code → Download ZIP** and extract it.

In VS Code, choose **File → Open Folder…** and select the `UCU-data-engineering` folder, which is the one containing `etl_pipeline.py`. Opening the parent folder instead makes VS Code's terminal start in the wrong place.

## 3. Create a virtual environment

A virtual environment keeps this project's packages separate from everything else on your machine.

Open the terminal in VS Code (**Terminal → New Terminal**, or `` Ctrl+` ``) and run:

```bash
python -m venv .venv
```

Activate it (PowerShell, the default VS Code terminal on Windows):

```bash
.venv\Scripts\Activate.ps1
```

The prompt now starts with `(.venv)`. If PowerShell says *running scripts is disabled on this system*, click the `˅` next to the `+` in the terminal panel, choose **Command Prompt**, and run this instead:

```bash
.venv\Scripts\activate.bat
```

On macOS or Linux the activation command is `source .venv/bin/activate`.

Then tell VS Code to use this environment: press `Ctrl+Shift+P`, type **Python: Select Interpreter**, and pick the entry that shows `.venv`. VS Code will now activate it automatically in new terminals.

## 4. Install the dependency

The only package needed is pandas. `sqlite3` comes with Python.

```bash
pip install -r requirements.txt
```

## 5. Run the pipeline

Either open `etl_pipeline.py` and click the **▷ Run Python File** button in the top-right corner, or run it from the terminal:

```bash
python etl_pipeline.py
```

You should see output like this:

```
[extract] 105 rows read from sales.csv
[transform] raw_rows: 105
[transform] duplicates_removed: 1
[transform] missing_required_removed: 1
[transform] bad_dates_removed: 0
[transform] non_positive_qty_removed: 1
[transform] clean_rows: 102
[validate] all checks passed
[transform] saved cleaned_sales.csv
[load] moved to cloud_storage_bucket/sales/2026/cleaned_sales.csv
[sql] loaded 102 rows into table `sales` (sales.db)

=== revenue_per_branch ===
 branch  transactions  total_revenue
Kampala            34       61395000
...
```

This console output is what to screenshot for deliverable iv.

## 6. Check the outputs

| What | Where |
|---|---|
| Cleaned data (Parts A and B) | `cloud_storage_bucket/sales/2026/cleaned_sales.csv` |
| SQLite database (Part C) | `sales.db` |
| Query results (Part C) | `query_outputs/*.csv` (one file per query) |

The CSV files open directly in VS Code or in Excel.

To browse `sales.db` inside VS Code, install the **SQLite Viewer** extension (publisher: Florian Klampfer) and click the file. You will see the `sales` table with 102 rows.

## 7. Run the SQL on its own (optional)

`etl_pipeline.py` runs `sales_analytics.sql` for you. To run the queries yourself, install the SQLite command-line tool from https://sqlite.org/download.html ("sqlite-tools" for Windows). Run the pipeline once first so `sales.db` has data, then in the terminal:

```bash
sqlite3 sales.db
```

At the `sqlite>` prompt, paste any of the four `SELECT` queries from `sales_analytics.sql`. Type `.headers on` and `.mode column` first to get readable tables, and `.quit` to leave.

Do not run the whole SQL file against `sales.db` with `sqlite3 sales.db < sales_analytics.sql`. The file starts with `DROP TABLE` and `CREATE TABLE`, so it wipes the table before the queries run, and the queries then return nothing.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'pandas'` | The virtual environment is not active, or VS Code is using a different interpreter. Check for `(.venv)` in the prompt, rerun step 3's **Select Interpreter**, then `pip install -r requirements.txt`. |
| `FileNotFoundError: ... sales.csv` | `sales.csv` is missing from the project folder. Download it again from the repo. |
| `AssertionError` from `[validate]` | Someone edited `sales.csv` and the cleaned data broke a rule. The message names the rule, such as `duplicate transaction_id`. Restore the original `sales.csv` from the repo. |
| `PermissionError` or `database is locked` | `sales.db` or a CSV is open in Excel, SQLite Viewer or another program. Close it and run again. |
