#!/bin/bash
# Test runner script for Kaaj

set -e

echo "🧪 Kaaj Test Suite"
echo "=================="
echo ""

# Check if PDF files exist
if [ ! -d "tests/assets" ] || [ -z "$(ls -A tests/assets/*.pdf 2>/dev/null)" ]; then
    echo "⚠️  Warning: No PDF files found in tests/assets/"
    echo "   Please add your test PDF files to tests/assets/ directory"
    echo ""
    exit 1
fi

PDF_COUNT=$(ls -1 tests/assets/*.pdf 2>/dev/null | wc -l)
echo "📄 Found $PDF_COUNT PDF file(s) in tests/assets/"
echo ""

# Check if TEST_DATABASE_URL is set
if [ -z "$TEST_DATABASE_URL" ]; then
    echo "⚠️  TEST_DATABASE_URL not set. Using default..."
    export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_kaaj"
    echo "   Using: $TEST_DATABASE_URL"
    echo ""
fi

# Parse command line arguments
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: ./run_tests.sh [options]"
    echo ""
    echo "Options:"
    echo "  -v, --verbose     Verbose output"
    echo "  -s, --stdout      Show print statements"
    echo "  -k EXPRESSION     Run tests matching EXPRESSION"
    echo "  --cov             Run with coverage report"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh                    # Run all tests"
    echo "  ./run_tests.sh -v                 # Verbose mode"
    echo "  ./run_tests.sh -k test_upload     # Run tests matching 'test_upload'"
    echo "  ./run_tests.sh --cov              # Run with coverage"
    echo ""
    exit 0
fi

# Run pytest with arguments
echo "🚀 Running tests..."
echo ""

pytest tests/ "$@"

echo ""
echo "✅ Tests completed!"

