"""
Algorithm A — Web Interface for Laboratory Use
================================================
Run with:
    streamlit run app.py
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

import streamlit as st

# Import core logic from the existing module
from alg_a import _fmt, algorithm_a, load_csv

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Algorithm A — Robust Statistics",
    page_icon="🔬",
    layout="centered",
)

st.title("🔬 Algorithm A — Robust Statistics")
st.caption(
    "ISO 13528-style robust mean and standard deviation for interlaboratory "
    "proficiency testing data."
)

# ---------------------------------------------------------------------------
# Sidebar: options
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Settings")

    value_column_input = st.text_input(
        "Value column",
        value="1",
        help="Column name (e.g. 'measurement') or 1-based index (e.g. '1').",
    )

    zscore_column_input = st.text_input(
        "Z-score column (optional)",
        value="",
        help="Optional column for z-score calculation. Leave blank to skip.",
    )

    precision = st.slider(
        "Output precision (significant digits)",
        min_value=4,
        max_value=15,
        value=6,
    )

    compat_excel = st.checkbox(
        "Excel-compatible convergence",
        value=True,
        help=(
            "Use the exact convergence rule from the workbook "
            "(x_new / 1 000 000). Disable for more robust handling of "
            "near-zero means."
        ),
    )

    max_iter = st.number_input(
        "Max iterations (safety cap)",
        min_value=10,
        max_value=10000,
        value=1000,
        step=100,
    )

    st.divider()
    st.download_button(
        "⬇️ Download sample CSV",
        data=Path("sample_input.csv").read_bytes(),
        file_name="sample_input.csv",
        mime="text/csv",
        help="Download a small example CSV to see the expected format.",
    )

# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------

uploaded = st.file_uploader(
    "Upload your CSV file",
    type=["csv"],
    help="The file must have a header row. Blank or non-numeric cells are ignored.",
)

if uploaded is None:
    st.info("Upload a CSV file to get started.")
    st.stop()

# ---------------------------------------------------------------------------
# Parse the uploaded file
# ---------------------------------------------------------------------------

raw_bytes = uploaded.read()
raw_text = raw_bytes.decode("utf-8-sig")

# Show a preview of the uploaded data
try:
    preview_rows = list(csv.reader(io.StringIO(raw_text)))
except Exception as exc:
    st.error(f"Could not parse CSV: {exc}")
    st.stop()

with st.expander("Preview uploaded data", expanded=False):
    if preview_rows:
        header = preview_rows[0]
        data_preview = preview_rows[1:11]  # first 10 rows
        st.write(f"**Columns:** {', '.join(header)}")
        st.write(f"**Rows (first 10 of {len(preview_rows) - 1}):**")
        st.table([dict(zip(header, row, strict=False)) for row in data_preview])

# ---------------------------------------------------------------------------
# Resolve column specification
# ---------------------------------------------------------------------------


def _resolve_col_from_text(spec_text: str, header: list[str]) -> str | int:
    """Return the column spec as int (1-based index) if numeric, else string."""
    spec = spec_text.strip()
    if not spec:
        raise ValueError("Value column must not be empty.")
    try:
        return int(spec)
    except ValueError:
        return spec


try:
    value_col_spec = _resolve_col_from_text(
        value_column_input, preview_rows[0] if preview_rows else []
    )
    zscore_col_spec: str | int | None = None
    if zscore_column_input.strip():
        zscore_col_spec = _resolve_col_from_text(
            zscore_column_input, preview_rows[0] if preview_rows else []
        )
except ValueError as exc:
    st.error(str(exc))
    st.stop()

# ---------------------------------------------------------------------------
# Run Algorithm A
# ---------------------------------------------------------------------------

if st.button("▶ Run Algorithm A", type="primary", use_container_width=True):
    # Save upload to a temporary in-memory path so load_csv can read it
    tmp_path = Path(uploaded.name)
    try:
        # Write to a temp file in the working directory
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as tmp:
            tmp.write(raw_bytes)
            tmp_name = tmp.name

        values, z_inputs = load_csv(Path(tmp_name), value_col_spec, zscore_col_spec)

    except Exception as exc:
        st.error(f"Error reading CSV: {exc}")
        st.stop()
    finally:
        try:
            os.unlink(tmp_name)
        except Exception:
            pass

    if not values:
        st.error("No numeric values found in the selected column. Check your column setting.")
        st.stop()

    # Run algorithm
    try:
        result = algorithm_a(values, compat_excel=compat_excel, max_iter=int(max_iter))
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()
    except Exception as exc:
        st.error(f"Algorithm A failed: {exc}")
        st.stop()

    # -----------------------------------------------------------------------
    # Display summary
    # -----------------------------------------------------------------------

    st.success(f"Completed in **{result['iterations']}** iteration(s).")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("n", result["n"])
    col2.metric("Median", _fmt(result["median"], precision))
    col3.metric("AlgA-mean", _fmt(result["robust_mean"], precision))
    col4.metric("AlgA-std", _fmt(result["robust_std"], precision))

    col5, col6, col7 = st.columns(3)
    col5.metric("s(MAD)", _fmt(result["s_mad"], precision))
    col6.metric("Iterations", result["iterations"])
    col7.metric("Max iter cap", int(max_iter))

    # -----------------------------------------------------------------------
    # Display data table
    # -----------------------------------------------------------------------

    st.subheader("Data Table")

    robust_mean = result["robust_mean"]
    robust_std = result["robust_std"]

    table_rows = []
    for i, (val, dev, adj) in enumerate(
        zip(result["sorted_values"], result["abs_dev"], result["adjusted"], strict=False), start=1
    ):
        row: dict = {
            "#": i,
            "Sorted value": val,
            "Abs. deviation": round(dev, 10),
            "Adjusted (AlgA)": round(adj, 10),
        }
        z_raw = z_inputs[i - 1] if i - 1 < len(z_inputs) else None
        if z_raw is not None and z_raw != "" and robust_std != 0.0:
            try:
                row["Z-score"] = round((float(z_raw) - robust_mean) / robust_std, 6)
            except ValueError:
                row["Z-score"] = z_raw
        table_rows.append(row)

    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    # -----------------------------------------------------------------------
    # Prepare CSV output for download
    # -----------------------------------------------------------------------

    csv_buf = io.StringIO()

    def write_csv_to_buf(buf: io.StringIO) -> None:
        writer = csv.writer(buf)
        writer.writerow(["A", "B", "C", "D", "E", "F", "G", "H", "I"])
        writer.writerow(
            [
                "",
                "",
                "median",
                _fmt(result["median"], precision),
                "AlgA-mean",
                _fmt(robust_mean, precision),
                "",
                "iterations:",
                str(result["iterations"]),
            ]
        )
        writer.writerow(
            [
                "",
                "",
                "s(MAD)",
                _fmt(result["s_mad"], precision),
                "AlgA-std",
                _fmt(robust_std, precision),
                "",
                "",
                "",
            ]
        )
        writer.writerow(
            [
                "",
                "",
                "number",
                str(result["n"]),
                "",
                "",
                "",
                "",
                "",
            ]
        )
        has_z = any(z is not None for z in z_inputs)
        writer.writerow(
            [
                "",
                "data",
                "abs. dev.",
                "number",
                "",
                "",
                "z_input" if has_z else "",
                "Zscore" if has_z else "",
                "",
            ]
        )
        for i, (val, dev, adj) in enumerate(
            zip(result["sorted_values"], result["abs_dev"], result["adjusted"], strict=False),
            start=1,
        ):
            z_raw = z_inputs[i - 1] if i - 1 < len(z_inputs) else None
            zscore_str = ""
            if z_raw is not None and z_raw != "" and robust_std != 0.0:
                try:
                    zscore_str = _fmt((float(z_raw) - robust_mean) / robust_std, precision)
                except ValueError:
                    zscore_str = z_raw
            writer.writerow(
                [
                    i,
                    _fmt(val, precision),
                    _fmt(dev, precision),
                    _fmt(adj, precision),
                    "",
                    "",
                    z_raw or "",
                    zscore_str,
                    "",
                ]
            )

    write_csv_to_buf(csv_buf)
    csv_bytes = csv_buf.getvalue().encode("utf-8")

    st.download_button(
        "⬇️ Download results as CSV",
        data=csv_bytes,
        file_name="alg_a_output.csv",
        mime="text/csv",
        use_container_width=True,
    )
