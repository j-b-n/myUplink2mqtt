#!/bin/bash
set -e

echo "=== myUplink2mqtt Setup Verification ==="
echo ""

echo "✓ Checking Python version..."
python --version
echo ""

echo "✓ Checking RUFF installation..."
ruff --version
echo ""

echo "✓ Checking pyproject.toml..."
if [ -f "pyproject.toml" ]; then
    echo "  Found: pyproject.toml"
    grep "name = " pyproject.toml | head -1
else
    echo "  ERROR: pyproject.toml not found"
    exit 1
fi
echo ""

echo "✓ Checking RUFF configuration..."
if [ -f ".ruff.toml" ]; then
    echo "  Found: .ruff.toml (primary)"
fi
echo ""

echo "✓ Checking requirements files..."
for file in requirements.txt requirements-dev.txt; do
    if [ -f "$file" ]; then
        echo "  Found: $file ($(wc -l < $file) lines)"
    fi
done
echo ""

echo "✓ Checking development files..."
for file in Makefile DEVELOPMENT.md MIGRATION_SUMMARY.md; do
    if [ -f "$file" ]; then
        echo "  Found: $file"
    fi
done
echo ""

echo "✓ Running RUFF format check..."
ruff format . --check 2>&1 | grep -E "^(Would reformat|already formatted|error)" || true
echo ""

echo "✓ Installed Python packages (key ones):"
pip list | grep -E "^(ruff|pytest|aiohttp|myuplink|paho-mqtt|requests-oauthlib)" || true
echo ""

echo "=== Setup Verification Complete ==="
echo ""
echo "Next steps:"
echo "  1. Review DEVELOPMENT.md for detailed information"
echo "  2. Run 'make format' to apply code formatting"
echo "  3. Run 'make check' to verify all checks pass"
echo "  4. Commit the new configuration files"
