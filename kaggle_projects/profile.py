"""Data profiling CLI: run ydata-profiling and extract key summary."""

import argparse
import glob
import json
import os
import sys
from pathlib import Path

import pandas as pd
import ydata_profiling
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(stderr=True)


def run_profiling(data_path, output_path):
    """Run ydata-profiling on all CSV files and return summary dicts."""
    os.makedirs(output_path, exist_ok=True)
    csv_files = glob.glob(f"{data_path}/*.csv")

    if not csv_files:
        console.print(f"[red]No CSV files found in {data_path}[/red]")
        sys.exit(1)

    summaries = []
    for file_path in csv_files:
        basename = os.path.basename(file_path)
        if "test" in basename.lower() or "submission" in basename.lower():
            console.print(f"[dim]Skipping {basename} (test/submission)[/dim]")
            continue

        console.print(f"[bold]Profiling[/bold] {basename}...")
        df = pd.read_csv(file_path)
        profile = ydata_profiling.ProfileReport(df, title=basename)

        stem = basename.replace(".csv", "")

        # Extract JSON first (warms internal cache), then save HTML (reuses cache)
        profile_json = profile.to_json()
        html_path = os.path.join(output_path, f"{stem}_profile.html")
        profile.to_file(html_path)

        profile_data = json.loads(profile_json)
        summary = extract_summary(profile_data, basename, df)
        summaries.append(summary)

        # Save concise summary JSON
        summary_path = os.path.join(output_path, f"{stem}_summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        console.print(f"  HTML: {html_path}")
        console.print(f"  Summary: {summary_path}")

    return summaries


def extract_summary(profile_data, filename, df):
    """Extract key metrics from ydata-profiling JSON into a concise summary."""
    table = profile_data.get("table", {})
    variables = profile_data.get("variables", {})

    # Dataset overview
    overview = {
        "rows": table.get("n"),
        "columns": table.get("n_var"),
        "missing_cells": table.get("n_cells_missing"),
        "missing_pct": table.get("p_cells_missing"),
        "duplicate_rows": table.get("n_duplicates"),
        "duplicate_pct": table.get("p_duplicates"),
    }

    # Per-column summary
    columns = {}
    for col_name, col_data in variables.items():
        col_summary = {
            "type": col_data.get("type"),
            "missing": col_data.get("n_missing"),
            "missing_pct": col_data.get("p_missing"),
            "distinct": col_data.get("n_distinct"),
            "distinct_pct": col_data.get("p_distinct"),
        }

        # Numeric-specific
        if col_data.get("type") == "Numeric":
            col_summary.update(
                {
                    "mean": col_data.get("mean"),
                    "std": col_data.get("std"),
                    "min": col_data.get("min"),
                    "max": col_data.get("max"),
                    "zeros": col_data.get("n_zeros"),
                    "zeros_pct": col_data.get("p_zeros"),
                    "skewness": col_data.get("skewness"),
                    "kurtosis": col_data.get("kurtosis"),
                }
            )

        # Categorical-specific
        if col_data.get("type") == "Categorical":
            col_summary["top_values"] = _extract_top_values(col_data)

        columns[col_name] = col_summary

    # Correlations (top pairs)
    correlations = _extract_top_correlations(profile_data)

    # Alerts from profiling
    alerts = []
    for alert in profile_data.get("alerts", []):
        if isinstance(alert, str):
            alerts.append(alert)
        elif isinstance(alert, dict):
            alerts.append(alert.get("alert_type", str(alert)))

    return {
        "filename": filename,
        "overview": overview,
        "columns": columns,
        "top_correlations": correlations,
        "alerts": alerts,
    }


def _extract_top_values(col_data, top_n=5):
    """Extract top N frequent values from categorical column."""
    value_counts = col_data.get("value_counts_without_nan")
    if not value_counts:
        return []
    if isinstance(value_counts, dict):
        sorted_items = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"value": k, "count": v} for k, v in sorted_items[:top_n]]
    return []


def _extract_top_correlations(profile_data, top_n=10):
    """Extract top N absolute correlations."""
    corr = profile_data.get("correlations", {})
    # Try pearson first
    pearson = corr.get("pearson", {})
    if not pearson:
        return []

    pairs = []
    seen = set()
    for col_a, col_corrs in pearson.items():
        if not isinstance(col_corrs, dict):
            continue
        for col_b, value in col_corrs.items():
            if col_a == col_b:
                continue
            key = tuple(sorted([col_a, col_b]))
            if key in seen:
                continue
            seen.add(key)
            if isinstance(value, (int, float)):
                pairs.append({"columns": list(key), "correlation": round(value, 4)})

    pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    return pairs[:top_n]


def print_summary(summary):
    """Print a concise summary to the terminal."""
    ov = summary["overview"]
    console.print(
        Panel(
            f"[bold]Rows:[/bold] {ov['rows']}  |  "
            f"[bold]Columns:[/bold] {ov['columns']}  |  "
            f"[bold]Missing:[/bold] {ov['missing_cells']} ({_pct(ov['missing_pct'])})  |  "
            f"[bold]Duplicates:[/bold] {ov['duplicate_rows']} ({_pct(ov['duplicate_pct'])})",
            title=summary["filename"],
            expand=False,
        )
    )

    # Column quality table
    table = Table(title="Column Summary", show_lines=True)
    table.add_column("Column", max_width=25)
    table.add_column("Type")
    table.add_column("Missing", justify="right")
    table.add_column("Distinct", justify="right")
    table.add_column("Notes", max_width=40)

    for col_name, col in summary["columns"].items():
        notes = []
        if col.get("missing_pct") and col["missing_pct"] > 0.05:
            notes.append(f"missing {_pct(col['missing_pct'])}")
        if col.get("zeros_pct") and col["zeros_pct"] > 0.3:
            notes.append(f"zeros {_pct(col['zeros_pct'])}")
        if col.get("skewness") and abs(col["skewness"]) > 2:
            notes.append(f"skew={col['skewness']:.1f}")
        if col.get("distinct_pct") and col["distinct_pct"] == 1.0:
            notes.append("unique")

        table.add_row(
            col_name,
            col.get("type", "?"),
            _pct(col.get("missing_pct")),
            str(col.get("distinct", "")),
            ", ".join(notes) if notes else "-",
        )

    console.print(table)

    # Top correlations
    if summary["top_correlations"]:
        console.print("\n[bold]Top Correlations:[/bold]")
        for pair in summary["top_correlations"][:5]:
            cols = " ↔ ".join(pair["columns"])
            console.print(f"  {cols}: {pair['correlation']}")

    # Alerts
    if summary["alerts"]:
        console.print(
            f"\n[bold yellow]Alerts ({len(summary['alerts'])}):[/bold yellow]"
        )
        for alert in summary["alerts"][:10]:
            console.print(f"  [yellow]• {alert}[/yellow]")


def _pct(value):
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Profile CSV data with ydata-profiling"
    )
    parser.add_argument(
        "data_path",
        help="Path to directory containing CSV files",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: <data_path>/../outputs/profiling)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output summary as JSON instead of table"
    )
    args = parser.parse_args(argv)

    data_path = args.data_path
    output_path = args.output
    if output_path is None:
        output_path = str(Path(data_path).parent / "outputs" / "profiling")

    summaries = run_profiling(data_path, output_path)

    for summary in summaries:
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print_summary(summary)


if __name__ == "__main__":
    main()
