#!/bin/bash
# Script para arreglar problemas de calidad de código

echo "🔧 Fixing code quality issues..."

# 1. Format with black
echo "📝 Running black..."
black src/agents/ src/schemas/ tests/ --line-length=100

# 2. Sort imports
echo "📦 Running isort..."
isort src/agents/ src/schemas/ tests/ --profile=black

# 3. Run linting to check
echo "🔍 Running pylint..."
pylint src/agents/ src/schemas/ --fail-under=8.5

echo "✅ Done! Now run tests:"
echo "pytest tests/unit/ -v --cov=src --cov-report=term-missing"
