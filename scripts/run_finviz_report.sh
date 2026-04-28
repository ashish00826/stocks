#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/Users/ashish/option_strategy"
ENV_FILE="$PROJECT_DIR/.env.finviz"
VENV_PY="$PROJECT_DIR/.venv/bin/python"
REPORT_SCRIPT="$PROJECT_DIR/scripts/finviz_report.py"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE"
  echo "Create it from .env.finviz.example and fill SMTP credentials."
  exit 1
fi

# Export key=value pairs from env file.
set -a
source "$ENV_FILE"
set +a

cd "$PROJECT_DIR"
exec "$VENV_PY" "$REPORT_SCRIPT"
