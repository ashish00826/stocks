#!/usr/bin/env python3
import json
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from finvizfinance.screener.overview import Overview

# Use raw Finviz filter codes to match MCP screener behavior.
# This preserves the same broader result set as your chat run.
FILTER_CODES = ",".join(
    [
        "fa_pe_u30",         # PE < 30
        "fa_roe_o25",        # ROE > 25%
        "fa_epsqoq_o50",     # Profit growth proxy: EPS QoQ > 50%
        "fa_salesqoq_o50",   # Sales growth QoQ > 50%
        "fa_debteq_u0.5",    # Debt/Equity < 0.5
        "sh_insiderown_o50", # Promoter holding proxy: Insider ownership > 50%
        "ta_sma200_pa",      # Price above 200-day MA
    ]
)

DEFAULT_RECIPIENTS = [
    "aaggarwal0826@gmail.com",
    "newbiztarseena@gmail.com",
]


def _split_csv_env(name: str, default_values):
    raw = os.getenv(name, "").strip()
    if not raw:
        return list(default_values)
    return [p.strip() for p in raw.split(",") if p.strip()]


def send_email_report(report_path: Path, rows_count: int):
    """Send report email using SMTP settings from env vars.

    Required env vars:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
    Optional:
      SMTP_FROM, REPORT_RECIPIENTS
    """
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()
    smtp_from = os.getenv("SMTP_FROM", smtp_user).strip()
    recipients = _split_csv_env("REPORT_RECIPIENTS", DEFAULT_RECIPIENTS)
    masked_user = smtp_user if len(smtp_user) <= 4 else f"{smtp_user[:2]}***{smtp_user[-2:]}"
    print(
        "SMTP debug: "
        f"host={smtp_host or '<empty>'}, "
        f"port={smtp_port}, "
        f"user={masked_user or '<empty>'}, "
        f"pass_len={len(smtp_pass)}, "
        f"from_set={'yes' if bool(smtp_from) else 'no'}, "
        f"recipients={len(recipients)}"
    )

    if not smtp_host or not smtp_user or not smtp_pass:
        print("Email skipped: set SMTP_HOST/SMTP_USER/SMTP_PASS to enable email.")
        return
    if not recipients:
        print("Email skipped: no recipients configured.")
        return

    subject = f"Finviz Daily Report - {datetime.now().strftime('%Y-%m-%d')}"
    body = (
        f"Attached is your Finviz report.\n\n"
        f"Rows: {rows_count}\n"
        f"Filter codes: {FILTER_CODES}\n"
        f"File: {report_path}\n"
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)
    msg.add_attachment(
        report_path.read_bytes(),
        maintype="application",
        subtype="json",
        filename=report_path.name,
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)
    print(f"Email sent to: {', '.join(recipients)}")


def run_report():
    foverview = Overview()
    # Bypass restrictive option mapping in finvizfinance and pass filter codes directly.
    foverview.request_params["f"] = FILTER_CODES
    df = foverview.screener_view()

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    day = datetime.now().strftime("%Y-%m-%d")
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / f"finviz_report_{ts}.json"
    df.to_json(out, orient="records", indent=2)
    latest = reports_dir / "finviz_latest.json"
    df.to_json(latest, orient="records", indent=2)
    dated_latest = reports_dir / f"finviz_latest_{day}.json"
    df.to_json(dated_latest, orient="records", indent=2)

    print(f"Wrote {len(df)} rows to {out}")
    print(f"Updated latest snapshot: {latest}")
    print(f"Updated dated snapshot: {dated_latest}")
    print(f"Applied filter codes: {FILTER_CODES}")
    send_email_report(dated_latest, len(df))

if __name__ == "__main__":
    run_report()
