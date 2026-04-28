#!/usr/bin/env python3
"""Generate a Finviz fundamentals report for cron usage.

Usage:
  python finviz_report.py
  python finviz_report.py --output-dir reports --format json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from finvizfinance.screener.overview import Overview


def build_filters() -> Dict[str, str]:
    """Baseline filter set matching the requested screen."""
    return {
        # PE Ratio < 30
        "P/E": "Under 30",
        # ROE > 25%
        "Return on Equity": "Over +25%",
        # EPS Positive (proxy in Finviz screener options)
        "EPS growththis year": "Positive (>0%)",
        # Profit Growth > 50% (closest available: EPS QoQ > 50%)
        "EPS growthqtr over qtr": "Over 50%",
        # Sales Growth > 50%
        "Sales growthqtr over qtr": "Over 50%",
        # Debt to Equity < 0.5
        "Debt/Equity": "Under 0.5",
        # Promoter holding proxy in Finviz: Insider Ownership
        "InsiderOwnership": "Over 50%",
        # Above 200 EMA proxy in Finviz screener: Price above SMA200
        "200-Day Simple Moving Average": "Price above SMA200",
    }


def fetch_rows(filters: Dict[str, str]) -> List[Dict[str, object]]:
    """Run screener and return records."""
    overview = Overview()
    overview.set_filter(filters_dict=filters)
    df = overview.screener_view()
    if df is None or df.empty:
        return []
    return df.to_dict(orient="records")


def write_report(rows: List[Dict[str, object]], output_dir: Path, fmt: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = output_dir / f"finviz_report_{stamp}.{fmt}"

    if fmt == "json":
        output_path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    else:
        # Minimal CSV writer without extra dependencies.
        if not rows:
            output_path.write_text("", encoding="utf-8")
        else:
            headers = list(rows[0].keys())
            lines = [",".join(headers)]
            for row in rows:
                vals = []
                for key in headers:
                    val = "" if row.get(key) is None else str(row.get(key))
                    val = '"' + val.replace('"', '""') + '"' if "," in val or '"' in val else val
                    vals.append(val)
                lines.append(",".join(vals))
            output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Finviz filtered stock report.")
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory to store generated reports (default: reports).",
    )
    parser.add_argument(
        "--format",
        choices=("json", "csv"),
        default="json",
        help="Output file format (default: json).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    filters = build_filters()
    rows = fetch_rows(filters)
    report_path = write_report(rows, Path(args.output_dir), args.format)

    print(f"Generated report: {report_path}")
    print(f"Rows: {len(rows)}")
    print("Applied filters:")
    for k, v in filters.items():
        print(f"- {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
