# Algorithm A — ISO 13528-style Robust Analysis

A Python implementation of **Algorithm A** from ISO 13528, reproducing the
behaviour of the Excel workbook `Algorithm-A.xls`.

Algorithm A computes a robust mean (*AlgA-mean*) and a robust standard
deviation (*AlgA-std*) by iteratively winsorizing the input data at
`x ± 1.5s` until convergence.

---

## Project layout

```
.
├── alg_a.py                  # Core Algorithm A — CLI and importable module
├── app.py                    # Streamlit web UI (browser-based, no CLI needed)
├── pyproject.toml            # Project metadata, ruff and pytest config
├── requirements.txt          # Runtime dependencies
├── requirements-dev.txt      # Dev/test dependencies (includes runtime)
├── Makefile                  # Developer convenience commands
├── .pre-commit-config.yaml   # Pre-commit hooks (lint + format on every commit)
├── .github/
│   └── workflows/ci.yml      # GitHub Actions CI (lint + tests on Python 3.10–3.12, Linux + Windows)
├── Launch Algorithm A.command # macOS double-click launcher
├── Launch Algorithm A.bat    # Windows double-click launcher
├── sample_input.csv          # 20-row example input
├── sample_input_84.csv       # 84-row synthetic example
├── sample_output.csv         # Output from sample_input.csv
├── sample_output_84.csv      # Output from sample_input_84.csv
└── tests/
    ├── test_alg_a.py         # 25 automated unit tests
    └── workbook_data.csv     # 84 values extracted from Algorithm-A.xls
```

---

## Setup (first time)

> Requires **Python ≥ 3.10**.

```bash
# 1. Clone / enter the project folder
cd mutu_algA

# 2. Set up an isolated virtual environment and install everything
make install-dev              # macOS / Linux — also works in Git Bash on Windows

# 3. Activate the virtual environment
source .venv/bin/activate    # macOS / Linux
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Windows (cmd):         .venv\Scripts\activate.bat
```

> **Windows without Git Bash?** Run the equivalent commands directly in PowerShell:
> ```powershell
> python -m venv .venv
> .venv\Scripts\Activate.ps1
> pip install --upgrade pip
> pip install -r requirements-dev.txt
> pre-commit install
> ```

This single command:
- Creates `.venv/` using the system Python
- Installs all runtime and dev dependencies into it
- Registers the pre-commit hooks so linting runs automatically on `git commit`

To install runtime dependencies only (e.g. on a server):

```bash
make install
```

<details>
<summary>Manual setup (without Make)</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements-dev.txt
pre-commit install
```

</details>

---

## Running the web app (lab users)

Laboratory users who do not need the command line can launch the browser-based
interface in one of two ways:

### Option A — double-click launcher

**macOS:** Double-click **`Launch Algorithm A.command`** in Finder.  
**Windows:** Double-click **`Launch Algorithm A.bat`** in Explorer.

A terminal window opens and the app loads automatically at `http://localhost:8501`.

> **macOS:** On the first launch the system may ask you to allow execution — click **Open**.  
> **Windows:** If you see a SmartScreen warning, click **More info → Run anyway**.

### Option B — terminal

```bash
make run                                        # macOS / Linux / Git Bash

# or, without Make:
.venv/bin/streamlit run app.py                  # macOS / Linux
.venv\Scripts\streamlit run app.py              # Windows
```

Then open `http://localhost:8501` in any browser.

**What the web app does:**

1. Upload any CSV file via drag-and-drop.
2. Enter the column name (e.g. `measurement`) or its 1-based index in the sidebar.
3. Click **▶ Run Algorithm A**.
4. View the summary metrics (n, median, AlgA-mean, AlgA-std, iterations) and the full data table.
5. Download the results as a CSV with **⬇ Download results as CSV**.

---

## Running the CLI

```bash
# macOS / Linux
.venv/bin/python alg_a.py sample_input.csv \
    --value-column measurement \
    --output sample_output.csv

# Windows
.venv\Scripts\python alg_a.py sample_input.csv ^
    --value-column measurement ^
    --output sample_output.csv
```

With a z-score column and XLSX export:

```bash
# macOS / Linux
.venv/bin/python alg_a.py input.csv \
    --value-column measurement \
    --zscore-column result \
    --output alg_a_output.csv \
    --output-xlsx alg_a_output.xlsx

# Windows
.venv\Scripts\python alg_a.py input.csv ^
    --value-column measurement ^
    --zscore-column result ^
    --output alg_a_output.csv ^
    --output-xlsx alg_a_output.xlsx
```

### Command-line reference

```
usage: alg_a.py [-h] [--value-column COL] [--zscore-column COL]
                [--output FILE] [--output-xlsx FILE]
                [--compat-excel | --no-compat-excel]
                [--max-iter N] [--precision DIGITS]
                input

positional arguments:
  input                 Path to the input CSV file.

options:
  --value-column COL    Column name (case-insensitive) or 1-based integer
                        index of the measurement column. Default: 1.
  --zscore-column COL   Optional column for z-score inputs (workbook column G).
  --output FILE         Output CSV path. Default: <input>_alg_a_output.csv.
  --output-xlsx FILE    Also write an XLSX workbook (requires openpyxl).
  --compat-excel        Use the exact workbook convergence rule
                        abs(x_new - x_old) < x_new / 1_000_000  (default).
  --no-compat-excel     Use a safer convergence rule
                        abs(x_new - x_old) < max(|x_new| / 1_000_000, 1e-12).
  --max-iter N          Iteration safety cap. Default: 1000.
  --precision DIGITS    Significant digits in output. Default: 15.
```

---

## Developer commands (Makefile)

| Command | What it does |
|---|---|
| `make install` | Create `.venv` and install runtime deps |
| `make install-dev` | Install all deps + register pre-commit hooks |
| `make test` | Run the full test suite with pytest |
| `make lint` | Run ruff linter |
| `make format` | Auto-format all Python files with ruff |
| `make run` | Launch the Streamlit web app |
| `make clean` | Remove `.venv`, caches, and `__pycache__` |

---

## Running the tests

```bash
make test                           # macOS / Linux / Git Bash

# or directly:
.venv/bin/pytest tests/ -v          # macOS / Linux
.venv\Scripts\pytest tests/ -v      # Windows
```

Expected result: **25 passed** (includes workbook reproduction test).

---

## Output CSV layout

The output mimics the workbook coordinate system (columns A–I):

```
A,B,C,D,E,F,G,H,I
,,median,<median>,AlgA-mean,<robust_mean>,,iterations:,<iterations>
,,s(MAD),<s_mad>,AlgA-std,<robust_std>,,,
,,number,<n>,,,,,
,data,abs. dev.,number,,,z_input,Zscore,
1,<val_1>,<abs_dev_1>,<adjusted_1>,,,<z_input_1>,<zscore_1>,
2,<val_2>,<abs_dev_2>,<adjusted_2>,,,<z_input_2>,<zscore_2>,
...
```

| Column | Workbook cell | Content |
|---|---|---|
| B | `B5:B…` | Input values, sorted ascending |
| C | `C5:C…` | `\|value − starting_median\|` |
| D | `D5:D…` | Winsorized/adjusted values from the final iteration |
| F row 1 | `F1` | AlgA-mean (robust mean) |
| F row 2 | `F2` | AlgA-std (robust std) |
| H | `H5:H…` | Z-scores: `(z_input − AlgA-mean) / AlgA-std` |

---

## Algorithm details

Given a numeric vector of `n` values:

1. Sort values ascending.
2. Compute the **starting median** (`D1`): `x = median(values)`.
3. Compute the **starting robust scale** (`D2`): `s = 1.483 × median(|value_i − x|)`.
4. Iterate:

   ```
   d = 1.5 × s
   adjusted_i = clamp(value_i, x − d, x + d)
   x = mean(adjusted)
   s = 1.134 × sample_std(adjusted)
   ```

   until `|x_new − x_old| < x_new / 1_000_000` (or the safer variant with
   `--no-compat-excel`).

Constants used:
- `1.483` — scale factor for the median absolute deviation (MAD).
  Do **not** substitute `1.4826`; the workbook uses `1.483`.
- `1.134` — correction factor for the robust standard deviation.
- `1.5`   — winsorization half-width multiplier.

Standard deviation uses the **sample formula** (`n−1` denominator), matching
Excel's `STDEV` function.

---

## Workbook reproduction

The values in `tests/workbook_data.csv` were extracted directly from
`Algorithm-A.xls` (sheet `AlgA`, cells `B5:B88`).  Running the CLI or the
web app against this file reproduces the original workbook results exactly:

| Output | Expected value |
|---|---:|
| Median (`D1`) | `29.0` |
| s(MAD) (`D2`) | `1.483` |
| Count (`D3`) | `84` |
| AlgA-mean (`F1`) | `28.698170211288396` |
| AlgA-std (`F2`) | `0.8352579792358779` |
| Iterations (`I1`) | `17` |

---

## CI / CD

Every push and pull request to `main` runs the GitHub Actions workflow in
`.github/workflows/ci.yml`:

1. **Pre-commit** — runs every hook in `.pre-commit-config.yaml` (trailing
   whitespace, YAML/TOML checks, ruff lint, ruff format) on Python 3.11.
2. **Test** — `pytest` + CLI smoke test across **6 combinations**: Python 3.10,
   3.11, 3.12 × Ubuntu and Windows.

All jobs must pass before a PR can be merged.

---

## Dependencies

| Dependency | Required for | Purpose |
|---|---|---|
| Python ≥ 3.10 | Everything | — |
| `streamlit ≥ 1.32` | Web app | Browser UI |
| `openpyxl ≥ 3.1` | CLI `--output-xlsx` | XLSX export |
| `pytest ≥ 8` | Tests | Test runner |
| `ruff ≥ 0.4` | Dev | Linter + formatter |
| `pre-commit ≥ 3.7` | Dev | Git hook runner |

The core Algorithm A logic (`alg_a.py`) uses **only the Python standard
library** and has no runtime dependencies.
