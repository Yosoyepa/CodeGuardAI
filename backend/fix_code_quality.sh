set -e
set -o pipefail

echo "🔧 Fixing code quality issues..."

echo "📝 Running black..."
if ! black src/agents/ src/schemas/ tests/ --line-length=100; then
    echo "❌ Black formatting failed"
    exit 1
fi

echo "📦 Running isort..."
if ! isort src/agents/ src/schemas/ tests/ --profile=black; then
    echo "❌ isort failed"
    exit 1
fi

echo "🔍 Running pylint..."
if ! pylint src/agents/ src/schemas/ --fail-under=8.5; then
    echo "❌ Pylint score below 8.5"
    exit 1
fi

echo "✅ All quality checks passed!"
echo ""
echo "Now run tests:"
echo "pytest tests/unit/ -v --cov=src --cov-report=term-missing"