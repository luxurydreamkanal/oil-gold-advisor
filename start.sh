#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Ropa & Zlato Advisor ==="
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Vytváram virtuálne prostredie..."
    python3 -m venv .venv
fi

# Activate
source .venv/bin/activate

# Install / upgrade dependencies silently
echo "Kontrolujem závislosti..."
pip install -q -r requirements.txt

echo ""
echo "Spúšťam aplikáciu na http://localhost:8501"
echo "Zastavenie: stlač Ctrl+C"
echo ""

streamlit run app.py --server.headless false
