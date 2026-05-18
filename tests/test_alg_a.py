"""Unit tests for alg_a.py — Algorithm A (ISO 13528-style robust analysis)."""

from __future__ import annotations

import csv
import math
import sys
import tempfile
from pathlib import Path

import pytest

# Allow importing alg_a from the project root regardless of how tests are run.
sys.path.insert(0, str(Path(__file__).parent.parent))

from alg_a import (
    algorithm_a,
    load_csv,
    median_excel,
    sample_std,
    write_csv,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WORKBOOK_DATA_CSV = Path(__file__).parent / "workbook_data.csv"
"""
Path to a CSV file containing the 84 measurement values from Algorithm-A.xls.
If the file is absent the workbook-reproduction test is skipped automatically.

To create this file:
  1. Open Algorithm-A.xls in Excel.
  2. Copy cells B5:B88 (the 84 values) to a new sheet.
  3. Save as workbook_data.csv with a single column header named 'measurement'.
"""


def approx(expected: float, tol: float = 1e-10) -> bool:
    """Return a pytest.approx instance for *expected* with absolute tolerance *tol*."""
    return pytest.approx(expected, abs=tol)


# ---------------------------------------------------------------------------
# 1. Workbook reproduction test
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not WORKBOOK_DATA_CSV.exists(),
    reason=(
        "tests/workbook_data.csv not found. "
        "Export the 84 measurement values from Algorithm-A.xls to this file "
        "with a single column header 'measurement' to enable this test."
    ),
)
def test_workbook_reproduction():
    """Reproduce the exact outputs of Algorithm-A.xls using the workbook values."""
    values, _ = load_csv(WORKBOOK_DATA_CSV, "measurement")
    result = algorithm_a(values, compat_excel=True)

    assert result["n"] == 84
    assert result["median"] == approx(29.0)
    assert result["s_mad"] == approx(1.483)
    assert result["robust_mean"] == approx(28.698170211288396)
    assert result["robust_std"] == approx(0.8352579792358779)
    assert result["iterations"] == 17


# ---------------------------------------------------------------------------
# 2. No-outlier simple case
# ---------------------------------------------------------------------------


def test_simple_no_outlier():
    """[10, 11, 12, 13, 14] — no outliers; should converge in one iteration."""
    values = [10.0, 11.0, 12.0, 13.0, 14.0]
    result = algorithm_a(values)

    assert result["n"] == 5
    assert result["median"] == approx(12.0)
    # MAD = median([2,1,0,1,2]) = 1.0  =>  s_mad = 1.483
    assert result["s_mad"] == approx(1.483)
    # All values within ±1.5*s of median; winsorization has no effect
    assert result["sorted_values"] == sorted(values)
    assert result["adjusted"] == sorted(values)
    assert result["robust_mean"] == approx(12.0)
    # sample_std([10,11,12,13,14]) = sqrt(2.5) ≈ 1.5811388
    expected_std = 1.134 * math.sqrt(2.5)
    assert result["robust_std"] == approx(expected_std, tol=1e-10)
    assert result["iterations"] == 1


def test_simple_no_outlier_abs_dev():
    """Absolute deviations must be computed against the *starting* median only."""
    values = [10.0, 11.0, 12.0, 13.0, 14.0]
    result = algorithm_a(values)
    expected_abs_dev = [2.0, 1.0, 0.0, 1.0, 2.0]
    for computed, expected in zip(result["abs_dev"], expected_abs_dev, strict=False):
        assert computed == approx(expected)


# ---------------------------------------------------------------------------
# 3. Outlier case
# ---------------------------------------------------------------------------


def test_outlier_winsorized():
    """[10, 11, 12, 13, 14, 100] — the extreme outlier must be capped."""
    values = [10.0, 11.0, 12.0, 13.0, 14.0, 100.0]
    result = algorithm_a(values)

    # The outlier (100) must be capped to something well below its original value
    last_adjusted = result["adjusted"]
    outlier_idx = result["sorted_values"].index(100.0)
    assert last_adjusted[outlier_idx] < 30.0, (
        "Outlier (100) should be heavily winsorized, not left at 100"
    )

    # Robust mean should be much closer to the bulk of the data than the arithmetic mean
    arith_mean = sum(values) / len(values)  # ≈ 26.67
    assert result["robust_mean"] < arith_mean * 0.6, (
        "Robust mean should be pulled away from the outlier compared to arithmetic mean"
    )

    # Robust standard deviation must be finite and positive
    assert result["robust_std"] > 0.0
    assert math.isfinite(result["robust_std"])

    # The n=6 result must match reference computation
    assert result["robust_mean"] == approx(12.870300454153949, tol=1e-8)
    assert result["robust_std"] == approx(2.901032055373042, tol=1e-8)


def test_outlier_iterations():
    """Outlier case must converge (iterations < max_iter)."""
    values = [10.0, 11.0, 12.0, 13.0, 14.0, 100.0]
    result = algorithm_a(values, max_iter=1000)
    assert result["iterations"] < 1000


# ---------------------------------------------------------------------------
# 4. Blank and non-numeric handling
# ---------------------------------------------------------------------------


def _write_csv_file(rows: list[list[str]], header: list[str]) -> Path:
    """Write a temporary CSV file and return its Path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    )
    writer = csv.writer(tmp)
    writer.writerow(header)
    writer.writerows(rows)
    tmp.close()
    return Path(tmp.name)


def test_blanks_ignored():
    """Blank cells in the measurement column are silently skipped."""
    path = _write_csv_file(
        [
            ["10"],
            [""],
            ["11"],
            [""],
            ["12"],
            ["13"],
            ["14"],
        ],
        ["measurement"],
    )
    values, _ = load_csv(path, "measurement")
    path.unlink()
    assert values == [10.0, 11.0, 12.0, 13.0, 14.0]


def test_non_numeric_ignored():
    """Non-numeric strings in the measurement column are silently skipped."""
    path = _write_csv_file(
        [
            ["10"],
            ["N/A"],
            ["11"],
            ["#VALUE!"],
            ["12"],
            ["13"],
            ["14"],
        ],
        ["measurement"],
    )
    values, _ = load_csv(path, "measurement")
    path.unlink()
    assert values == [10.0, 11.0, 12.0, 13.0, 14.0]


def test_mixed_blanks_and_non_numeric():
    """Mixed blanks and non-numeric entries are all skipped."""
    path = _write_csv_file(
        [["10"], [""], ["bad"], ["12"], [""], ["14"]],
        ["val"],
    )
    values, _ = load_csv(path, "val")
    path.unlink()
    assert values == [10.0, 12.0, 14.0]


# ---------------------------------------------------------------------------
# 5. Small n
# ---------------------------------------------------------------------------


def test_n1_does_not_crash():
    """n=1 should run without error; AlgA-std is defined as 0.0."""
    result = algorithm_a([42.0])
    assert result["n"] == 1
    assert result["median"] == approx(42.0)
    assert result["s_mad"] == approx(0.0)
    assert result["robust_mean"] == approx(42.0)
    assert result["robust_std"] == 0.0  # sample_std([42]) → 0.0
    assert result["iterations"] >= 1


def test_n0_raises():
    """n=0 must raise ValueError with a clear message."""
    with pytest.raises(ValueError, match="[Nn]o numeric"):
        algorithm_a([])


# ---------------------------------------------------------------------------
# 6. Core statistical helpers
# ---------------------------------------------------------------------------


def test_median_excel_odd():
    assert median_excel([3.0, 1.0, 2.0]) == pytest.approx(2.0)


def test_median_excel_even():
    assert median_excel([1.0, 2.0, 3.0, 4.0]) == pytest.approx(2.5)


def test_median_excel_single():
    assert median_excel([7.0]) == pytest.approx(7.0)


def test_median_excel_empty():
    with pytest.raises(ValueError):
        median_excel([])


def test_sample_std_matches_excel():
    """sample_std must match Excel STDEV (n-1 denominator)."""
    values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    # mean=5, sum-sq-dev = 9+1+1+1+0+0+4+16 = 32, variance = 32/7
    # Excel STDEV([2,4,4,4,5,5,7,9]) = sqrt(32/7)
    assert sample_std(values) == pytest.approx(math.sqrt(32.0 / 7.0))


def test_sample_std_two_values():
    assert sample_std([3.0, 5.0]) == pytest.approx(math.sqrt(2.0))


def test_sample_std_one_value():
    assert sample_std([99.0]) == 0.0


# ---------------------------------------------------------------------------
# 7. Sorting guarantee
# ---------------------------------------------------------------------------


def test_values_sorted_ascending():
    """Input values must be sorted ascending before calculation."""
    unsorted = [14.0, 10.0, 12.0, 11.0, 13.0]
    result = algorithm_a(unsorted)
    assert result["sorted_values"] == [10.0, 11.0, 12.0, 13.0, 14.0]


# ---------------------------------------------------------------------------
# 8. Convergence safety cap
# ---------------------------------------------------------------------------


def test_max_iter_respected():
    """RuntimeError must be raised if algorithm does not converge within max_iter."""
    # The outlier dataset [10,11,12,13,14,100] normally needs 31 iterations;
    # capping at 5 must raise RuntimeError before convergence.
    with pytest.raises(RuntimeError, match="[Cc]onverg"):
        algorithm_a([10.0, 11.0, 12.0, 13.0, 14.0, 100.0], max_iter=5)


# ---------------------------------------------------------------------------
# 9. CSV output layout
# ---------------------------------------------------------------------------


def test_write_csv_layout():
    """write_csv must produce the expected column-A-to-I layout."""
    values = [10.0, 11.0, 12.0, 13.0, 14.0]
    result = algorithm_a(values)
    z_inputs = ["10.0", "11.0", "12.0", "13.0", "14.0"]

    with tempfile.NamedTemporaryFile(
        suffix=".csv", delete=False, mode="w", newline="", encoding="utf-8"
    ) as tmp:
        out_path = Path(tmp.name)

    write_csv(out_path, result, z_inputs)

    with out_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    out_path.unlink()

    # Row 0: column labels A–I
    assert rows[0] == ["A", "B", "C", "D", "E", "F", "G", "H", "I"]

    # Row 1: median / AlgA-mean / iterations
    assert rows[1][2] == "median"
    assert rows[1][4] == "AlgA-mean"
    assert rows[1][7] == "iterations:"
    assert int(rows[1][8]) == result["iterations"]

    # Row 2: s(MAD) / AlgA-std
    assert rows[2][2] == "s(MAD)"
    assert rows[2][4] == "AlgA-std"

    # Row 3: number / n
    assert rows[3][2] == "number"
    assert int(rows[3][3]) == result["n"]

    # Row 4: column header row
    assert rows[4][1] == "data"
    assert rows[4][2] == "abs. dev."
    assert rows[4][3] == "number"

    # Data rows start at index 5
    data_rows = rows[5:]
    assert len(data_rows) == result["n"]
    for idx, row in enumerate(data_rows, start=1):
        assert int(row[0]) == idx
        assert float(row[1]) == pytest.approx(result["sorted_values"][idx - 1])
        assert float(row[2]) == pytest.approx(result["abs_dev"][idx - 1])
        assert float(row[3]) == pytest.approx(result["adjusted"][idx - 1])


# ---------------------------------------------------------------------------
# 10. column lookup by name and by index
# ---------------------------------------------------------------------------


def test_load_csv_by_name():
    path = _write_csv_file([["10.5"], ["11.0"], ["12.5"]], ["measurement"])
    values, _ = load_csv(path, "measurement")
    path.unlink()
    assert values == pytest.approx([10.5, 11.0, 12.5])


def test_load_csv_by_index():
    path = _write_csv_file([["10.5"], ["11.0"], ["12.5"]], ["measurement"])
    values, _ = load_csv(path, 1)  # 1-based index
    path.unlink()
    assert values == pytest.approx([10.5, 11.0, 12.5])


def test_load_csv_bad_column_name():
    path = _write_csv_file([["10.5"]], ["measurement"])
    with pytest.raises(ValueError, match="not found"):
        load_csv(path, "nonexistent")
    path.unlink()


# ---------------------------------------------------------------------------
# 11. compat_excel vs. robust convergence
# ---------------------------------------------------------------------------


def test_no_compat_excel_converges():
    """--no-compat-excel mode must also converge for standard positive data."""
    values = [10.0, 11.0, 12.0, 13.0, 14.0]
    result = algorithm_a(values, compat_excel=False)
    assert result["robust_mean"] == pytest.approx(12.0)


def test_compat_excel_and_no_compat_agree_positive_data():
    """For positive data both convergence rules should give the same final answer."""
    values = [10.0, 11.0, 12.0, 13.0, 14.0, 100.0]
    r1 = algorithm_a(values, compat_excel=True)
    r2 = algorithm_a(values, compat_excel=False)
    assert r1["robust_mean"] == pytest.approx(r2["robust_mean"], abs=1e-6)
    assert r1["robust_std"] == pytest.approx(r2["robust_std"], abs=1e-6)
