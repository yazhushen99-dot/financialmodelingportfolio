"""Compare real native outputs with the shipped Python reference outputs.

Run AFTER executing the Stata/EViews script; this does not run either application.
No native output is fabricated. Missing output files are reported as NOT RUN.
"""

from pathlib import Path
import argparse
import csv
import math

ROOT = Path(__file__).resolve().parents[1]
ALIASES = {
    "driver": "driver_regression",
    "trend": "trend_and_seasonality",
    "naive": "seasonal_naive",
}


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def close(actual, expected, label, errors):
    if not math.isclose(float(actual), float(expected), rel_tol=1e-7, abs_tol=1e-6):
        errors.append(f"{label}: native={actual}; reference={expected}")


def check_metrics(path, reference, errors):
    rows = read_rows(path)
    if {row["model"] for row in rows} != set(ALIASES):
        errors.append(f"{path.name}: expected exactly driver, trend and naive models")
    for row in rows:
        model = row["model"]
        if model not in ALIASES:
            continue
        diffs = [float(item[ALIASES[model]]) - float(item["revenue_musd"]) for item in reference]
        actuals = [float(item["revenue_musd"]) for item in reference]
        expected = {
            "n": len(reference),
            "mae_musd": sum(abs(value) for value in diffs) / len(diffs),
            "rmse_musd": math.sqrt(sum(value * value for value in diffs) / len(diffs)),
            "mape_pct": 100 * sum(abs(value) / actual for value, actual in zip(diffs, actuals)) / len(diffs),
        }
        for metric, value in expected.items():
            close(row[metric], value, f"{path.name}/{model}/{metric}", errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", choices=["stata", "eviews", "all"], default="all")
    args = parser.parse_args()
    reference = read_rows(ROOT / "analysis/forecast_validation.csv")
    future = read_rows(ROOT / "analysis/forecast_2026.csv")
    errors = []
    checked = []
    absent = []
    for tool in (["stata", "eviews"] if args.tool == "all" else [args.tool]):
        if tool == "stata":
            folder = ROOT / "analysis/native_stata"
            required = [folder / "validation_metrics.csv", folder / "validation_predictions.csv", folder / "forecast_2026.csv"]
        else:
            required = [ROOT / "analysis/eviews_validation_metrics.csv", ROOT / "analysis/eviews_annual_forecasts.csv"]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
        if missing:
            absent.append(tool)
            print(f"NOT RUN: {tool}; missing: {', '.join(missing)}")
            continue
        check_metrics(required[0], reference, errors)
        if tool == "stata":
            for path, expected_rows, prefix in [(required[1], reference, "pred_"), (required[2], future, "forecast_")]:
                rows = read_rows(path)
                actual_by_date = {row["date"]: row for row in rows}
                if len(rows) != len(expected_rows) or set(actual_by_date) != {row["date"] for row in expected_rows}:
                    errors.append(f"{path.name}: date keys or row count differ")
                    continue
                for expected in expected_rows:
                    actual = actual_by_date[expected["date"]]
                    for native_name, reference_name in ALIASES.items():
                        close(actual[prefix + native_name], expected[reference_name], f"{path.name}/{expected['date']}/{native_name}", errors)
        else:
            rows = read_rows(required[1])
            if {row["model"] for row in rows} != set(ALIASES):
                errors.append("EViews annual forecasts: model set differs")
            for row in rows:
                if row["model"] in ALIASES:
                    total = sum(float(item[ALIASES[row["model"]]]) for item in future)
                    close(row["2026_revenue_musd"], total, f"EViews annual/{row['model']}", errors)
        checked.append(tool)
    if errors:
        print("PARITY FAILED")
        print("\n".join(errors))
        return 1
    if checked:
        print("PARITY PASSED: " + ", ".join(checked))
    if absent:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
